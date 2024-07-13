import datetime
import json
import spacy
import re

from django.core.management import BaseCommand
from django.db import IntegrityError
from fuzzywuzzy import process

from apps.company.models import Industries, Roles, CompanyProfile, SalaryRange, Job, Skill, Certs
from apps.core.models import CustomUser

# Load the spaCy model
nlp = spacy.load("en_core_web_sm")

def parse_salary(salary):
    print(f"Parsing salary: {salary}")
    if salary is None:
        print(f"Parsing None")
        return "None", "None"
    parts = salary.split(' ')[1].split('-')
    return int(parts[0]), int(parts[1])


def match_closest(query, choices):
    closest_match = process.extractOne(query, choices)
    return closest_match[0] if closest_match else query


def clean_employment_type(employment_type):
    return employment_type.lower().replace('-', ' ')


def get_or_create_industry(industry_name, existing_industries):
    print(f"Industry {industry_name}")
    closest_match = match_closest(industry_name, existing_industries)
    print(f"Closest match: {closest_match}")

    if closest_match:
        print("Already exists")
        industry = Industries.objects.get(name=closest_match)
        print("Pulled")
    else:
        print("Creating industry")
        industry = Industries.objects.create(name=industry_name)

    return industry

def get_or_create_role(role_name, common_roles):
    role_name = match_closest(role_name, common_roles)
    role, created = Roles.objects.get_or_create(name=role_name)
    return role


def extract_skills(description, skills_list, certs_list):
    # Define a list of common skills for initial matching
    skills = skills_list
    certs = certs_list

    # Process the text using spaCy
    doc = nlp(description)

    # Initialize sets for the different types of skills
    required_skills = set()
    nice_to_have_skills = set()
    certs_skills = set()

    # Extract skills based on predefined list
    for token in doc:
        if token.text.lower() in [skill.lower() for skill in skills]:
            required_skills.add(token.text)
        if token.text.lower() in [cert.lower() for cert in certs]:
            certs_skills.add(token.text)

    # Extract skills from bullet points or requirement sections
    lines = description.split('\n')
    for line in lines:
        line = line.strip()
        if re.match(r'•', line) or 'required skills' in line.lower() or 'preferred skills' in line.lower() or 'certifications' in line.lower():
            for skill in skills:
                if re.search(r'\b' + re.escape(skill) + r'\b', line, re.IGNORECASE):
                    if 'nice to have' in line.lower() or 'preferred' in line.lower():
                        nice_to_have_skills.add(skill)
                    else:
                        required_skills.add(skill)
            for cert in certs:
                if re.search(r'\b' + re.escape(cert) + r'\b', line, re.IGNORECASE):
                    certs_skills.add(cert)

    print(f"Extracted required skills: {len(required_skills)}, nice to have skills: {len(nice_to_have_skills)}, certs: {len(certs_skills)}")
    return list(required_skills), list(nice_to_have_skills), list(certs_skills)


def add_skills_to_db(extracted_skills, model):
    print(f"Extracting {model} skills: {extracted_skills}")
    skills = []
    for skill_name in extracted_skills:
        print(f"Skill name: {skill_name}")
        skill, created = model.objects.get_or_create(name=skill_name)
        if created:
            print(f"Created new {model.__name__}: {skill_name}")
        skills.append(skill)
    return skills

def extract_role(title, common_roles):
    role_name = match_closest(title, common_roles)
    return role_name


def process_job_data(job_data, common_roles, common_skills, common_certs, existing_industries):
    print("get ready")
    if Job.objects.filter(external_id=job_data["id"]).exists():
        print("Job already exists")
        return
    created_date = datetime.datetime.strptime(job_data["created"], '%Y-%m-%d %H:%M:%S')
    print(job_data["id"])
    if created_date < datetime.datetime(2024, 5, 1):
        print("skipping job")
        return
    print("check company")

    company_profiles = CompanyProfile.objects.filter(company_name=job_data["company_name"])
    if company_profiles.exists():
        company_profile = company_profiles.first()
    else:
        company_profile = CompanyProfile.objects.create(
            company_name=job_data["company_name"],
            company_url=job_data["company_url"],
            is_unclaimed_account=True,
            coresignal_id=job_data["company_id"]
        )
    print(f"Company Profile: {company_profile}")
    industry = get_or_create_industry(job_data["job_industries_collection"][0]["job_industry_list"]["industry"], existing_industries)
    if industry:
        print(f"industry found {industry}")
        print(f"Adding to profile")
        company_profile.industries.add(industry)
        company_profile.save()
        print(f"Saved to profile")

    min_salary, max_salary = parse_salary(job_data["salary"])
    print("done")
    min_salary_range = SalaryRange.objects.filter(range__gte=min_salary).first()
    print("done ===")
    max_salary_range = SalaryRange.objects.filter(range__lte=max_salary).first()
    print("done ***")

    print("ROLE (((")
    role_name = extract_role(job_data["title"], common_roles)
    role = get_or_create_role(role_name, common_roles)
    print("ROLE found ^^^")
    print("SKILLS search %%%")

    required_skills, nice_to_have_skills, certs_skills = extract_skills(job_data["description"], common_skills, common_certs)
    print("Adding SKILLS ###")

    required_skills_objs = add_skills_to_db(required_skills, Skill)
    nice_to_have_skills_objs = add_skills_to_db(nice_to_have_skills, Skill)
    certs_objs = add_skills_to_db(certs_skills, Skill)
    print("SKILLS found $$$")

    job = Job.objects.create(
        external_id=job_data["id"],
        job_title=job_data["title"],
        external_description=job_data["description"],
        job_type=clean_employment_type(job_data["employment_type"]),
        location=job_data["location"],
        url=job_data["url"],
        min_compensation=min_salary_range,
        max_compensation=max_salary_range,
        parent_company=company_profile,
        role=role,
        status='active'
    )

    for skill in required_skills_objs:
        job.skills.add(skill)
    for skill in nice_to_have_skills_objs:
        job.nice_to_have_skills.add(skill)
    for cert in certs_objs:
        job.certs.add(cert)

        job.save()
        print("job saved {}".format(job.id))


class Command(BaseCommand):
    help = 'Processes job data and stores it in the database'

    def add_arguments(self, parser):
        parser.add_argument('json_file', type=str, help='The JSON file containing job data')

    def handle(self, *args, **kwargs):
        json_file = kwargs['json_file']

        try:
            with open(json_file, 'r') as file:
                job_data_list = json.load(file)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File "{json_file}" not found'))
            return
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'File "{json_file}" is not a valid JSON file'))
            return

        # Pull common roles, skills, certs, and industries once at the top
        common_roles = list(Roles.objects.values_list('name', flat=True))
        common_skills = list(Skill.objects.values_list('name', flat=True))
        common_certs = list(Certs.objects.values_list('name', flat=True))
        existing_industries = list(Industries.objects.values_list('name', flat=True))

        for job_data in job_data_list:
            process_job_data(job_data, common_roles, common_skills, common_certs, existing_industries)
            self.stdout.write(self.style.SUCCESS(f'Successfully processed job data for job ID {job_data["id"]}'))

        self.stdout.write(self.style.SUCCESS('Successfully processed all job data'))
