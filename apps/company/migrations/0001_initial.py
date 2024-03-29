# Generated by Django 4.1.3 on 2023-09-23 07:46

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django_quill.fields


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CompanyProfile",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("is_unclaimed_account", models.BooleanField(default=False)),
                ("company_name", models.CharField(max_length=200)),
                ("job_post_credit", models.IntegerField(default=0)),
                ("job_feature_credit", models.IntegerField(default=0)),
                ("tag_line", django_quill.fields.QuillField(blank=True, null=True)),
                ("mission", django_quill.fields.QuillField()),
                ("vision", django_quill.fields.QuillField(blank=True, null=True)),
                (
                    "company_highlights",
                    django_quill.fields.QuillField(blank=True, null=True),
                ),
                (
                    "company_diversity_statement",
                    django_quill.fields.QuillField(blank=True, null=True),
                ),
                (
                    "company_benefits",
                    django_quill.fields.QuillField(blank=True, null=True),
                ),
                (
                    "company_size",
                    models.CharField(
                        choices=[
                            ("1 - 20", "1 - 20"),
                            ("21 - 100", "21 - 100"),
                            ("101 - 500", "101 - 500"),
                            ("501 - 1000", "501 - 1000"),
                            ("1001 - 5000", "1001 - 5000"),
                            ("5001", "5001"),
                        ],
                        max_length=11,
                    ),
                ),
                ("is_startup", models.BooleanField(null=True)),
                (
                    "startup_funding_series_stage",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("Pre Seed", "Pre Seed"),
                            ("Seed", "Seed"),
                            ("Series A", "Series A"),
                            ("Series B", "Series B"),
                            ("Series C", "Series C"),
                            ("Series D", "Series D"),
                            ("Series E", "Series E"),
                            ("Series F", "Series F"),
                        ],
                        max_length=8,
                        null=True,
                    ),
                ),
                (
                    "ethics_statement",
                    django_quill.fields.QuillField(blank=True, null=True),
                ),
                (
                    "logo",
                    models.ImageField(
                        default="default-logo.jpeg", upload_to="logo_pics"
                    ),
                ),
                (
                    "background_img",
                    models.ImageField(
                        default="company_backgrounds/default-background.png",
                        upload_to="company_backgrounds",
                    ),
                ),
                ("company_url", models.URLField(blank=True, null=True)),
                ("linkedin", models.URLField(blank=True, null=True)),
                ("twitter", models.URLField(blank=True, null=True)),
                ("youtube", models.URLField(blank=True, null=True)),
                ("facebook", models.URLField(blank=True, null=True)),
                ("instagram", models.URLField(blank=True, null=True)),
                ("location", models.CharField(blank=True, max_length=200, null=True)),
                ("board_total", models.IntegerField(blank=True, null=True)),
                ("female_board_total", models.IntegerField(blank=True, null=True)),
                ("poc_board_total", models.IntegerField(blank=True, null=True)),
                ("black_board_total", models.IntegerField(blank=True, null=True)),
                ("indigenous_board_total", models.IntegerField(blank=True, null=True)),
                ("lgbtqia_board_total", models.IntegerField(blank=True, null=True)),
                ("disabled_board_total", models.IntegerField(blank=True, null=True)),
                ("leadership_total", models.IntegerField(blank=True, null=True)),
                ("female_c_level_total", models.IntegerField(blank=True, null=True)),
                ("poc_c_level_total", models.IntegerField(blank=True, null=True)),
                ("black_c_level_total", models.IntegerField(blank=True, null=True)),
                (
                    "indigenous_c_level_total",
                    models.IntegerField(blank=True, null=True),
                ),
                ("lgbtqia_c_level_total", models.IntegerField(blank=True, null=True)),
                ("disabled_c_level_total", models.IntegerField(blank=True, null=True)),
                ("covid_plan", django_quill.fields.QuillField(blank=True, null=True)),
                ("pay_transparency", models.BooleanField(default=False)),
                ("promotion_transparency", models.BooleanField(default=False)),
                ("remote_work", models.BooleanField(default=False)),
                ("company_outings", models.BooleanField(default=False)),
                ("erg", models.BooleanField(default=False)),
                ("flexible_working", models.BooleanField(default=False)),
                ("entertainment", models.BooleanField(default=False)),
                ("holidays", models.BooleanField(default=False)),
                ("career_frameworks", models.BooleanField(default=False)),
                (
                    "career_frameworks_details",
                    django_quill.fields.QuillField(blank=True, null=True),
                ),
                ("internships", models.BooleanField(default=False)),
                ("apprenticeships", models.BooleanField(default=False)),
                ("mentorship_programs", models.BooleanField(default=False)),
                (
                    "onboarding_plans",
                    django_quill.fields.QuillField(blank=True, null=True),
                ),
                ("relocation_assistance", models.BooleanField(default=False)),
                ("menstrual_leave", models.BooleanField(default=False)),
                ("unlimited_pto", models.BooleanField(default=False)),
                ("pto", models.BooleanField(default=False)),
                ("health_insurance", models.BooleanField(default=False)),
                ("life_insurance", models.BooleanField(default=False)),
                ("dental_insurance", models.BooleanField(default=False)),
                ("vision_insurance", models.BooleanField(default=False)),
                ("retirement_plans", models.BooleanField(default=False)),
                ("retirement_plans_matching", models.BooleanField(default=False)),
                ("hsa", models.BooleanField(default=False)),
                ("fsa", models.BooleanField(default=False)),
                ("long_term_disability", models.BooleanField(default=False)),
                ("short_term_disability", models.BooleanField(default=False)),
                ("tuition_reimbursement", models.BooleanField(default=False)),
                ("financial_education", models.BooleanField(default=False)),
                ("student_debt_refinancing", models.BooleanField(default=False)),
                (
                    "education_budget_total",
                    models.CharField(blank=True, max_length=140, null=True),
                ),
                ("education_budget", models.BooleanField(default=False)),
                ("childcare_benefits", models.BooleanField(default=False)),
                ("childcare_stipends", models.BooleanField(default=False)),
                ("paid_parental_leave", models.BooleanField(default=False)),
                (
                    "paid_parental_leave_details",
                    django_quill.fields.QuillField(blank=True, null=True),
                ),
                ("gym_benefits", models.BooleanField(default=False)),
                ("mental_health_stipend", models.BooleanField(default=False)),
                ("wellness_program", models.BooleanField(default=False)),
                ("sabbatical", models.BooleanField(default=False)),
                ("office_setup", models.BooleanField(default=False)),
                ("wifi_reimbursement", models.BooleanField(default=False)),
                ("cellphone_reimbursement", models.BooleanField(default=False)),
                ("donation_matching", models.BooleanField(default=False)),
                ("service_hours", models.BooleanField(default=False)),
                ("family_planning", models.BooleanField(default=False)),
                ("adoption_assistance", models.BooleanField(default=False)),
                ("ivf", models.BooleanField(default=False)),
                ("family_medical_leave", models.BooleanField(default=False)),
                ("pet_friendly", models.BooleanField(default=False)),
                ("pet_insurances", models.BooleanField(default=False)),
                ("car_chargers", models.BooleanField(default=False)),
                ("in_office_snacks", models.BooleanField(default=False)),
                ("in_office_cafeteria", models.BooleanField(default=False)),
                ("stocks", models.BooleanField(default=False)),
                ("laundry", models.BooleanField(default=False)),
                ("commuting_reimbursement", models.BooleanField(default=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now_add=True)),
                (
                    "stripe_customer_id",
                    models.CharField(blank=True, max_length=200, null=True),
                ),
                ("confirm_service_agreement", models.BooleanField(default=False)),
                (
                    "account_creator",
                    models.OneToOneField(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile_as_account_creator",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "account_owner",
                    models.ManyToManyField(
                        related_name="company_account_owner",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CompanySubscriptionCodes",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=100, unique=True)),
                ("amounts", models.IntegerField(null=True)),
                ("number", models.IntegerField()),
            ],
        ),
        migrations.CreateModel(
            name="CompanyTypes",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=300)),
                ("created_at", models.DateTimeField(auto_now=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Department",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=300, unique=True)),
                ("created_at", models.DateTimeField(auto_now=True)),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="Industries",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=300)),
                ("webflow_item_id", models.CharField(max_length=400)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name="JobLevel",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("level", models.CharField(blank=True, max_length=20, null=True)),
                ("expertise", models.CharField(blank=True, max_length=8, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="SalaryRange",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("range", models.CharField(max_length=8)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name="Skill",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(max_length=300)),
                ("webflow_item_id", models.CharField(max_length=400)),
                (
                    "skill_type",
                    models.CharField(
                        choices=[("skill", "skill"), ("tool", "tool")],
                        default="skill",
                        max_length=5,
                    ),
                ),
                (
                    "job_roles_wf_id",
                    models.CharField(blank=True, max_length=300, null=True),
                ),
                ("slug", models.CharField(blank=True, max_length=300, null=True)),
                (
                    "job_postings_wf_id",
                    models.CharField(blank=True, max_length=300, null=True),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Roles",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("name", models.CharField(blank=True, max_length=1000, null=True)),
                ("is_analytical_heavy", models.BooleanField(default=False)),
                ("is_customer_facing", models.BooleanField(default=False)),
                ("is_travel_common", models.BooleanField(default=False)),
                ("is_high_meeting_frequency", models.BooleanField(default=False)),
                ("is_active_in_career_programing", models.BooleanField(default=False)),
                ("description", django_quill.fields.QuillField(blank=True, null=True)),
                (
                    "creativity_level",
                    models.CharField(
                        choices=[
                            ("light", "light"),
                            ("medium", "medium"),
                            ("heavy", "heavy"),
                        ],
                        default="light",
                        max_length=10,
                    ),
                ),
                (
                    "communications_level",
                    models.CharField(
                        choices=[
                            ("light", "light"),
                            ("medium", "medium"),
                            ("heavy", "heavy"),
                        ],
                        default="light",
                        max_length=10,
                    ),
                ),
                (
                    "independent_work_level",
                    models.CharField(
                        choices=[
                            ("light", "light"),
                            ("medium", "medium"),
                            ("heavy", "heavy"),
                        ],
                        default="light",
                        max_length=10,
                    ),
                ),
                ("slug", models.CharField(blank=True, max_length=1000, null=True)),
                (
                    "webflow_id",
                    models.CharField(blank=True, max_length=1000, null=True),
                ),
                ("job_post", models.CharField(blank=True, max_length=1000, null=True)),
                (
                    "job_skills",
                    models.CharField(blank=True, max_length=1480, null=True),
                ),
                (
                    "level_of_interaction",
                    models.CharField(
                        choices=[
                            ("working_independently", "working independently"),
                            ("working_as_a_team", "working as a team"),
                        ],
                        max_length=25,
                    ),
                ),
                (
                    "level_of_responsibility",
                    models.CharField(
                        choices=[
                            ("light", "light"),
                            ("medium", "medium"),
                            ("heavy", "heavy"),
                        ],
                        default="light",
                        max_length=25,
                    ),
                ),
                (
                    "level_of_decision_making",
                    models.CharField(
                        choices=[
                            ("light", "light"),
                            ("medium", "medium"),
                            ("heavy", "heavy"),
                        ],
                        default="light",
                        max_length=25,
                    ),
                ),
                (
                    "type_of_work",
                    models.CharField(
                        choices=[
                            ("creative_work", "Creative work"),
                            ("logical_work", "Logical work"),
                            ("analytical_work", "Analytical work"),
                        ],
                        default="logical_work",
                        max_length=20,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("changed_at", models.DateTimeField(auto_now=True, null=True)),
                (
                    "job_skill_list",
                    models.ManyToManyField(
                        related_name="role_skills", to="company.skill"
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="InterviewRequest",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("date_requested", models.DateTimeField(auto_now_add=True)),
                ("interview_date", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("ACCEPTED", "Accepted"),
                            ("DECLINED", "Declined"),
                        ],
                        default="PENDING",
                        max_length=50,
                    ),
                ),
                ("notes", models.TextField(blank=True, null=True)),
                (
                    "candidate",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "company",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        to="company.companyprofile",
                    ),
                ),
            ],
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="account_subscription_status",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="company.companysubscriptioncodes",
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="billing_team",
            field=models.ManyToManyField(
                related_name="company_billing_team", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="company_types",
            field=models.ManyToManyField(
                blank=True, related_name="company_types", to="company.companytypes"
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="current_employees",
            field=models.ManyToManyField(
                related_name="company_current_employees", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="hiring_team",
            field=models.ManyToManyField(
                related_name="company_hiring_team", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="industries",
            field=models.ManyToManyField(to="company.industries"),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="internal_account_manager",
            field=models.ManyToManyField(
                related_name="managed_companies", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="internal_recruiting_team",
            field=models.ManyToManyField(
                related_name="recruiting_for_companies", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="past_employees",
            field=models.ManyToManyField(
                related_name="past_companies", to=settings.AUTH_USER_MODEL
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="referral_employees",
            field=models.ManyToManyField(
                blank=True,
                default=[],
                related_name="company_employees",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="companyprofile",
            name="unclaimed_account_creator",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="profile_as_unclaimed_account_creator",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
    ]
