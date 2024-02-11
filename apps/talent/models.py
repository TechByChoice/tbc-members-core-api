from django.db import models
from django_quill.fields import QuillField

from apps.company.models import (
    CompanyTypes,
    SalaryRange,
    Industries,
    Roles,
    Department,
    Skill,
    JobLevel,
)
from apps.core.models import CustomUser, CommunityNeeds


# Create your models here.


class TalentProfile(models.Model):
    ACTIVE = "Yes"
    CLOSED = "No"

    STATUS_CHOICE = ((ACTIVE, "Yes"), (CLOSED, "No"))
    user = models.OneToOneField(
        CustomUser, related_name="user", on_delete=models.CASCADE
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
    job_level = models.ForeignKey(
        JobLevel,
        on_delete=models.CASCADE,
        related_name="talents_job_level",
        null=True,
        blank=True,
        db_constraint=False,
    )
    skills = models.ManyToManyField(
        Skill, related_name="talent_skills_list", blank=False
    )
    department = models.ManyToManyField(
        Department, related_name="talent_department_list", blank=False
    )
    tech_journey = models.CharField(max_length=10, choices=CAREER_JOURNEY, default=1)

    resume = models.FileField(null=True, blank=True, upload_to="resumes")

    role = models.ManyToManyField(Roles, related_name="talent_role_types")
    industries = models.ManyToManyField(Industries, blank=True)
    company_types = models.ManyToManyField(CompanyTypes, blank=True)
    is_talent_status = models.BooleanField(default=False)
    # board level folks
    role_c_level = models.BooleanField(default=False)
    experience_board = models.BooleanField(default=False)
    experience_c_level = models.BooleanField(default=False)
    experience_advisory = models.BooleanField(default=False)
    experience_vp = models.BooleanField(default=False)
    experience_director = models.BooleanField(default=False)
    time_commitment_monthly = models.BooleanField(default=False)
    time_commitment_quarterly = models.BooleanField(default=False)
    time_commitment_bi_annually = models.BooleanField(default=False)
    time_commitment_annually = models.BooleanField(default=False)
    # compensation
    compensation_paid = models.BooleanField(default=False)
    compensation_equity = models.BooleanField(default=False)
    compensation_cash = models.BooleanField(default=False)
    compensation_none = models.BooleanField(default=False)

    min_compensation = models.ForeignKey(
        SalaryRange,
        related_name="min_salary_range",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )
    max_compensation = models.ForeignKey(
        SalaryRange,
        related_name="max_salary_range",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
    )

    # tbc_program_interest = models.ManyToManyField(CommunityNeeds)
    # TODO | CHANGE COMPANY PROFILE -> TalentConnections TO KEEP TACK OF CONNECTIONS MADE
    # connected_company = models.ManyToManyField(CompanyProfile, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " profile"
