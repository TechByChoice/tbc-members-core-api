from django.db import models
from django_quill.fields import QuillField

from apps.core.models import CustomUser

ONSITE = "On-site"
HYBRID = "Hybrid"
REMOTE = "Remote"

ON_SITE_REMOTE = (
    (ONSITE, "On-site"),
    (HYBRID, "Hybrid"),
    (REMOTE, "Remote"),
    ("unknown", "unknown"),
)
COMPANY_SIZE = (
    ("unknown", "unknown"),
    ("1 - 20", "1 - 20"),
    ("21 - 100", "21 - 100"),
    ("101 - 500", "101 - 500"),
    ("501 - 1000", "501 - 1000"),
    ("1001 - 5000", "1001 - 5000"),
    ("5001", "5001"),
)

CAREER_JOURNEY = (
    ("1", "0 years"),
    ("2", "1 - 2 years"),
    ("3", "3 - 5 years"),
    ("4", "6 - 10 years"),
    ("5", "11 - 15  years"),
    ("6", "16 - 20 years"),
    ("7", "21+ years"),
)


class Skill(models.Model):
    name = models.CharField(max_length=300)
    webflow_item_id = models.CharField(max_length=400)
    SKILL = "skill"
    TOOL = "tool"
    STATUS_CHOICE = ((SKILL, "skill"), (TOOL, "tool"))
    skill_type = models.CharField(max_length=5, choices=STATUS_CHOICE, default=SKILL)
    # job_roles = models.ForeignKey('Roles', on_delete=models.CASCADE, null=True, blank=True)
    job_roles_wf_id = models.CharField(max_length=300, null=True, blank=True)
    slug = models.CharField(max_length=300, null=True, blank=True)
    # job_postings = models.ForeignKey('Job', on_delete=models.CASCADE, null=True, blank=True)
    job_postings_wf_id = models.CharField(max_length=300, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name


class Industries(models.Model):
    name = models.CharField(max_length=300)
    webflow_item_id = models.CharField(max_length=400, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # @property
    def __str__(self):
        return self.name


class Certs(models.Model):
    name = models.CharField(max_length=300)
    details = models.CharField(max_length=800, blank=True, null=True)
    roles = models.CharField(max_length=800, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # @property
    def __str__(self):
        return self.name


class Department(models.Model):
    name = models.CharField(max_length=300, unique=True)
    created_at = models.DateTimeField(auto_now=True)
    changed_at = models.DateTimeField(auto_now_add=True)

    # @property
    def __str__(self):
        return self.name


class Roles(models.Model):
    name = models.CharField(max_length=1000, null=True, blank=True)
    is_analytical_heavy = models.BooleanField(default=False)
    is_customer_facing = models.BooleanField(default=False)
    is_travel_common = models.BooleanField(default=False)
    is_high_meeting_frequency = models.BooleanField(default=False)
    is_active_in_career_programing = models.BooleanField(default=False)
    description = QuillField(blank=True, null=True)

    LIGHT = "light"
    MEDIUM = "medium"
    HEAVY = "heavy"

    LEVEL_CHOICE = ((LIGHT, "light"), (MEDIUM, "medium"), (HEAVY, "heavy"))

    TYPE_OF_WORK_CHOICES = (
        ("creative_work", "Creative work"),
        ("logical_work", "Logical work"),
        ("analytical_work", "Analytical work"),
    )

    TYPE_OF_INTERACTIONS = (
        ("working_independently", "working independently"),
        ("working_as_a_team", "working as a team"),
    )
    creativity_level = models.CharField(
        max_length=10, choices=LEVEL_CHOICE, default=LIGHT
    )
    communications_level = models.CharField(
        max_length=10, choices=LEVEL_CHOICE, default=LIGHT
    )
    independent_work_level = models.CharField(
        max_length=10, choices=LEVEL_CHOICE, default=LIGHT
    )
    slug = models.CharField(max_length=1000, null=True, blank=True)
    webflow_id = models.CharField(max_length=1000, null=True, blank=True)
    job_post = models.CharField(max_length=1000, null=True, blank=True)
    job_skills = models.CharField(max_length=1480, null=True, blank=True)
    job_skill_list = models.ManyToManyField(Skill, related_name="role_skills")
    level_of_interaction = models.CharField(max_length=25, choices=TYPE_OF_INTERACTIONS)
    level_of_responsibility = models.CharField(
        max_length=25, choices=LEVEL_CHOICE, default=LIGHT
    )
    level_of_decision_making = models.CharField(
        max_length=25, choices=LEVEL_CHOICE, default=LIGHT
    )
    type_of_work = models.CharField(
        max_length=20, choices=TYPE_OF_WORK_CHOICES, default="logical_work"
    )
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    changed_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    # @property
    def __str__(self):
        return self.name if self.name else ""


class SalaryRange(models.Model):
    range = models.CharField(max_length=8)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.range


class JobLevel(models.Model):
    level = models.CharField(max_length=20, null=True, blank=True)
    expertise = models.CharField(max_length=8, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.level


class CompanyTypes(models.Model):
    name = models.CharField(max_length=300)
    created_at = models.DateTimeField(auto_now=True)
    updated_at = models.DateTimeField(auto_now=True)

    # @property
    def __str__(self):
        return self.name


class CompanyProfile(models.Model):
    # DIFFERENT USER GROUPS RELATION
    # person who made the account: full access
    talent_choice_account = models.BooleanField(default=False)
    account_creator = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="profile_as_account_creator",
    )
    # if the company was added from a referral or someone adding it to their profile
    unclaimed_account_creator = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="profile_as_unclaimed_account_creator",
    )
    is_unclaimed_account = models.BooleanField(blank=False, null=False, default=False)
    # can update billing details
    billing_team = models.ManyToManyField(
        CustomUser, related_name="company_billing_team"
    )
    # can view & interact with talent
    hiring_team = models.ManyToManyField(CustomUser, related_name="company_hiring_team")
    # can edit company details
    account_owner = models.ManyToManyField(
        CustomUser, related_name="company_account_owner"
    )
    current_employees = models.ManyToManyField(
        CustomUser, related_name="company_current_employees"
    )
    past_employees = models.ManyToManyField(CustomUser, related_name="past_companies")
    # This is their tbc support person
    internal_account_manager = models.ManyToManyField(
        CustomUser, related_name="managed_companies"
    )
    # These are the TBC Community Recruiters
    internal_recruiting_team = models.ManyToManyField(
        CustomUser, related_name="recruiting_for_companies"
    )
    # Non admins cannot edit the account details but they can own a referral based job
    referral_employees = models.ManyToManyField(
        CustomUser, related_name="company_employees", blank=True, default=[]
    )
    company_types = models.ManyToManyField(
        CompanyTypes, related_name="company_types", blank=True
    )

    company_name = models.CharField(max_length=400)
    industries = models.ManyToManyField(Industries, blank=True)

    tag_line = models.CharField(max_length=3000, blank=True, null=True)
    mission = models.CharField(max_length=7000, blank=True, null=True)
    vision = models.CharField(max_length=7000, blank=True, null=True)
    company_highlights = models.CharField(max_length=3000, blank=True, null=True)
    company_diversity_statement = models.CharField(max_length=3000, blank=True, null=True)
    company_benefits = models.CharField(max_length=3000, blank=True, null=True)
    # ethics
    company_size = models.CharField(max_length=13, choices=COMPANY_SIZE)
    is_startup = models.BooleanField(blank=False, null=True)
    SERIES_STAGE = (
        ("Pre Seed", "Pre Seed"),
        ("Seed", "Seed"),
        ("Series A", "Series A"),
        ("Series B", "Series B"),
        ("Series C", "Series C"),
        ("Series D", "Series D"),
        ("Series E", "Series E"),
        ("Series F", "Series F"),
    )
    startup_funding_series_stage = models.CharField(
        max_length=8, choices=SERIES_STAGE, blank=True, null=True
    )
    ethics_statement = models.CharField(max_length=3000, blank=True, null=True)
    logo = models.ImageField(default="default-logo.jpeg", upload_to="logo_pics")
    logo_url = models.URLField(max_length=400, blank=True, null=True)
    background_img = models.ImageField(
        default="company_backgrounds/default-background.png",
        upload_to="company_backgrounds",
    )
    company_url = models.URLField(max_length=400, blank=True, null=True)
    linkedin = models.URLField(blank=True, null=True, max_length=200)
    twitter = models.URLField(blank=True, null=True, max_length=200)
    youtube = models.URLField(blank=True, null=True, max_length=200)
    facebook = models.URLField(blank=True, null=True, max_length=200)
    instagram = models.URLField(blank=True, null=True, max_length=200)
    location = models.CharField(blank=True, null=True, max_length=200)
    state = models.CharField(blank=True, null=True, max_length=200)
    city = models.CharField(blank=True, null=True, max_length=200)
    postal_code = models.CharField(blank=True, null=True, max_length=200)
    coresignal_id = models.CharField(blank=True, null=True, max_length=60)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.company_name

    @classmethod
    def filter(cls, user):
        pass


class Job(models.Model):
    # post_title = models.CharField(max_length=300)
    external_id = models.CharField(max_length=140, blank=True, null=True)
    job_title = models.CharField(max_length=140, blank=False, null=False)
    description = QuillField(blank=True, null=True)
    external_description = models.CharField(max_length=20000, blank=True, null=True)
    level = models.ForeignKey(JobLevel, on_delete=models.CASCADE, blank=True, null=True)
    url = models.CharField(max_length=300)
    interview_process = QuillField(blank=True, null=True)
    external_interview_process = models.CharField(
        max_length=3000, blank=True, null=True
    )
    FULL_TIME = "full time"
    PART_TIME = "part time"
    CONTRACT = "contract"
    VOLUNTEER = "volunteer"
    TEMPORARY = "temporary"
    INTERNSHIP = "internship"
    APPRENTICESHIP = "apprenticeship"

    JOB_TYPE_CHOICE = (
        (FULL_TIME, "full time"),
        (PART_TIME, "part time"),
        (CONTRACT, "contracting"),
        (CONTRACT, "contracting"),
        (VOLUNTEER, "volunteer"),
        (TEMPORARY, "temporary"),
        (INTERNSHIP, "internship"),
        (APPRENTICESHIP, "apprenticeship"),
    )
    job_type = models.CharField(
        max_length=14, choices=JOB_TYPE_CHOICE, default=FULL_TIME
    )
    job_type_str = models.CharField(max_length=300, null=True, blank=True)

    ACTIVE = "active"
    PENDING = "pending"
    PAUSE = "pause"
    DRAFT = "draft"
    CLOSED = "closed"

    STATUS_CHOICE = (
        (DRAFT, "Draft"),
        (PAUSE, "Pause"),
        (ACTIVE, "Active"),
        (PENDING, "Pending"),
        (CLOSED, "Closed"),
        ("job_expired", "Job Expired"),
        ("company_details_needed", "Company Details Needed"),
        ("job_details_needed", "Job Details Needed"),
        ("rejected_bad_company", "Rejected Bad Company"),
        ("rejected_role_alignment", "Rejected Role Alignment"),
    )
    department = models.ManyToManyField(Department, blank=True)
    skills = models.ManyToManyField(Skill, blank=True)
    certs = models.ManyToManyField(Certs, blank=True)
    nice_to_have_skills = models.ManyToManyField(Skill, blank=True, related_name="nice_to_have_skills")

    status = models.CharField(max_length=23, choices=STATUS_CHOICE, default=DRAFT)

    on_site_remote = models.CharField(
        max_length=7, choices=ON_SITE_REMOTE, default="unknown", blank=False, null=False
    )

    compensation_paid = models.BooleanField(default=False)
    compensation_equity = models.BooleanField(default=False)
    compensation_none = models.BooleanField(default=False)

    compensation_range = models.CharField(max_length=100, null=True, blank=True)
    #
    min_compensation = models.ForeignKey(
        SalaryRange,
        related_name="min_salary_band",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    max_compensation = models.ForeignKey(
        SalaryRange,
        related_name="max_salary_band",
        on_delete=models.CASCADE,
        blank=True,
        null=True,
    )
    #
    role = models.ForeignKey(
        Roles,
        related_name="job_role_types",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    experience = models.BooleanField(default=False, null=True, blank=True)

    years_of_experience = models.CharField(
        max_length=10, choices=CAREER_JOURNEY, null=True, blank=True
    )
    pub_date = models.DateTimeField("date published", auto_now=True)
    sourced_talent_from_us = models.BooleanField(default=False)
    featured_job = models.BooleanField(default=False)
    is_referral_job = models.BooleanField(default=False)
    referral_note = models.TextField(max_length=1000, blank=True, null=True)

    team_size = models.IntegerField(null=True, blank=True)
    female_team_size_total = models.IntegerField(null=True, blank=True)
    poc_team_size_total = models.IntegerField(null=True, blank=True)
    black_team_size_total = models.IntegerField(null=True, blank=True)
    indigenous_team_size_total = models.IntegerField(null=True, blank=True)
    lgbtqia_team_size_total = models.IntegerField(null=True, blank=True)
    disabled_team_size_total = models.IntegerField(null=True, blank=True)

    department_size = models.IntegerField(null=True, blank=True)
    female_department_size_total = models.IntegerField(null=True, blank=True)
    poc_department_size_total = models.IntegerField(null=True, blank=True)
    black_department_size_total = models.IntegerField(null=True, blank=True)
    indigenous_department_size_total = models.IntegerField(null=True, blank=True)
    lgbtqia_department_size_total = models.IntegerField(null=True, blank=True)
    disabled_department_size_total = models.IntegerField(null=True, blank=True)
    is_paid = models.BooleanField(default=False, null=True)
    parent_company = models.ForeignKey(
        CompanyProfile, on_delete=models.CASCADE, default=False, null=True
    )

    is_remote = models.BooleanField(default=False, null=False)
    location = models.CharField(max_length=100, null=True, blank=True)

    created_by = models.ManyToManyField(
        CustomUser, null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # INTEGRATIONS
    lever_id = models.CharField(max_length=200, null=True, blank=True)
    lever_api_key = models.CharField(max_length=200, null=True, blank=True)
    is_pull_remoteio = models.BooleanField(default=False, null=False)

    class Meta:
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return self.job_title + " at " + self.parent_company.company_name
