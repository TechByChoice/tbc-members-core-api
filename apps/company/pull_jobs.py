import datetime
from fuzzywuzzy import process

from models import Industries, Roles, CompanyProfile, SalaryRange, Job


def parse_salary(salary):
    if salary is None:
        return None, None
    parts = salary.split(' ')[1].split('-')
    return int(parts[0]), int(parts[1])


def match_closest(query, choices):
    closest_match = process.extractOne(query, choices)
    return closest_match[0] if closest_match else query


def clean_employment_type(employment_type):
    return employment_type.lower().replace('-', ' ')


def get_or_create_industry(industry_name):
    industry, created = Industries.objects.get_or_create(
        name=match_closest(industry_name, Industries.objects.values_list('name', flat=True)))
    return industry


def get_or_create_role(role_name):
    role, created = Roles.objects.get_or_create(
        name=match_closest(role_name, Roles.objects.values_list('name', flat=True)))
    return role


def match_skills(description, skills_list):
    matched_skills = []
    for skill in skills_list:
        if process.extractOne(skill.name, [description]):
            matched_skills.append(skill)
    return matched_skills


def process_job_data(job_data):
    created_date = datetime.datetime.strptime(job_data["created"], '%Y-%m-%d %H:%M:%S')
    if created_date < datetime.datetime(2024, 6, 1):
        return

    company_profile, created = CompanyProfile.objects.get_or_create(
        company_name=job_data["company_name"],
        defaults={
            "company_url": job_data["company_url"]
        }
    )

    industry = get_or_create_industry(job_data["job_industries_collection"][0]["job_industry_list"]["industry"])
    company_profile.industries.add(industry)
    company_profile.save()

    min_salary, max_salary = parse_salary(job_data["salary"])
    min_salary_range = SalaryRange.objects.filter(range__gte=min_salary).first()
    max_salary_range = SalaryRange.objects.filter(range__lte=max_salary).first()

    role = get_or_create_role(job_data["job_functions_collection"][0]["job_function_list"]["function"])
    skills = match_skills(job_data["description"], role.job_skill_list.all())

    job = Job.objects.create(
        external_id=job_data["id"],
        job_title=job_data["title"],
        department=job_data["department"],
        external_description=job_data["description"],
        job_type=clean_employment_type(job_data["employment_type"]),
        location=job_data["location"],
        url=job_data["url"],
        min_compensation=min_salary_range,
        max_compensation=max_salary_range,
        parent_company=company_profile,
        role=role,
        created_by=None,  # Set the appropriate user
    )

    for skill in skills:
        job.skills.add(skill)

    job.save()


# Sample JSON data
job_data = {
    "id": 241190097,
    "created": "2024-03-22 12:13:03",
    "last_updated": "2024-06-20 14:41:42",
    "time_posted": "3 months ago",
    "title": "Sales Representative",
    "description": "Calling all Sales Trailblazers! ...",
    "employment_type": "Full-time",
    "location": "Ashland, OH",
    "url": "https://www.linkedin.com/jobs/view/sales-representative-at-spherion-mid-ohio-3862183095",
    "salary": "USD 65000-75000",
    "job_functions_collection": [{
        "id": 192588801,
        "job_id": 241190097,
        "function_id": 2,
        "deleted": 0,
        "created": "2024-03-22 12:13:03",
        "last_updated": "2024-03-22 12:13:03",
        "job_function_list": {
            "id": 2,
            "created": "2020-08-14 14:04:10",
            "last_updated": "2020-08-14 14:04:10",
            "function": "Sales",
            "hash": "11ff9f68afb6b8b5b8eda218d7c83a65"
        }
    }],
    "job_industries_collection": [{
        "id": 239666760,
        "job_id": 241190097,
        "industry_id": 44,
        "deleted": 0,
        "created": "2024-03-22 12:13:03",
        "last_updated": "2024-03-22 12:13:03",
        "job_industry_list": {
            "id": 44,
            "created": "2020-08-14 14:11:51",
            "last_updated": "2020-08-14 14:11:51",
            "industry": "Staffing and Recruiting",
            "hash": "616bdfe5a21ece9b1c2e4f54c6b4182c"
        }
    }]
}

process_job_data(job_data)
