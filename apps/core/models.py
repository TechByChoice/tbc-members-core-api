import datetime
import json
import logging

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.db import models
from django.utils import timezone
from django_quill.fields import QuillField

from utils.sendgrid_helper import remove_user_from_convertkit
from utils.slack import deactivate_slack_user, send_invite

# Create your models here.
CHOICES = ((None, "Prefer not to answer"), (True, "Yes"), (False, "No"))
logger = logging.getLogger(__name__)


class CustomUserManager(BaseUserManager):
    """
    Custom user model manager where email is the unique identifiers
    for authentication instead of usernames.
    """
    use_in_migrations = True

    def get_queryset(self):
        """
        Return a queryset of active (non-deleted) users.
        """
        return super().get_queryset().filter(is_deleted=False)

    def all_with_deleted(self):
        """
        Return a queryset of all users, including deleted ones.
        """
        return super().get_queryset()

    def _create_user(self, email, password, **extra_fields):
        """
        Create and save a User with the given email and password.
        """
        if not email:
            raise ValueError("Users require an email field")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError("Enter a valid email address")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Create and save a SuperUser with the given email and password.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class CustomUser(AbstractBaseUser):
    """
    Custom User model with email as the unique identifier and additional fields for soft deletion.
    """
    username = None
    email = models.EmailField(unique=True, validators=[validate_email])
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)
    # account types
    is_staff = models.BooleanField(default=False)
    is_recruiter = models.BooleanField(default=False)
    is_member = models.BooleanField(default=False)
    is_talent_choice = models.BooleanField(default=False)
    is_member_onboarding_complete = models.BooleanField(default=False)
    is_onboarding_reminder_sent = models.BooleanField(default=False)
    onboarding_reminder_sent_date = models.DateTimeField(blank=True, null=True)
    is_migrated_account = models.BooleanField(default=False)
    # Open Doors
    is_open_doors = models.BooleanField(default=False)
    is_open_doors_onboarding_complete = models.BooleanField(default=False)
    is_open_doors_profile_complete = models.BooleanField(default=False)
    # mentorship program
    is_mentor = models.BooleanField(default=False)
    is_mentee = models.BooleanField(default=False)
    is_mentor_profile_active = models.BooleanField(default=False)
    is_mentor_profile_removed = models.BooleanField(default=False)
    is_mentor_training_complete = models.BooleanField(default=False)
    is_mentor_interviewing = models.BooleanField(default=False)
    is_mentor_profile_paused = models.BooleanField(default=False)
    is_mentor_profile_approved = models.BooleanField(default=False)
    is_mentor_application_submitted = models.BooleanField(default=False)
    is_talent_source_beta = models.BooleanField(default=False)
    # speaker
    is_speaker = models.BooleanField(default=False)
    # team
    is_volunteer = models.BooleanField(default=False)
    is_team = models.BooleanField(default=False)
    # TalentChoice
    is_community_recruiter = models.BooleanField(default=False)
    is_company_account = models.BooleanField(default=False)
    is_email_confirmation_sent = models.BooleanField(default=False)
    is_email_confirmed = models.BooleanField(default=False)
    is_company_onboarding_complete = models.BooleanField(default=False)
    # Partnership
    is_partnership = models.BooleanField(default=False)
    # Reviews
    is_company_review_access_active = models.BooleanField(default=False)
    company_review_tokens = models.IntegerField(
        default=3,
    )
    ip_address = models.CharField(blank=True, null=True, max_length=280)
    is_superuser = models.BooleanField(default=False)
    joined_at = models.DateTimeField(auto_now_add=True)
    email_confirmed = models.BooleanField(default=False)
    is_sendgrid_invite_sent = models.BooleanField(default=False)
    # slack
    slack_user_id = models.CharField(max_length=20, blank=True, null=True)
    is_slack_active = models.BooleanField(default=False, blank=True, null=True)
    is_slack_invite_sent = models.BooleanField(default=False, blank=True, null=True)
    is_slack_found_with_user_email = models.BooleanField(default=False, blank=True, null=True)
    # delete users
    is_deleted = models.BooleanField(default=False)
    deleted_at = models.DateTimeField(null=True, blank=True)
    deletion_reason = models.CharField(max_length=50, null=True, blank=True)
    last_modified = models.DateTimeField(auto_now=True)


    DELETION_REASONS = [
        ('test_account', 'Test Account'),
        ('user_requested', 'User Requested'),
        ('broke_coc', 'Broke Code of Conduct'),
        ('spam', 'Spam'),
    ]

    objects = CustomUserManager()
    active_objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    def soft_delete(self, reason):
        """
        Soft delete the user account.

        Args:
            reason (str): The reason for deletion, must be one of DELETION_REASONS.

        Raises:
            ValueError: If an invalid reason is provided.
        """
        self.is_deleted = True
        self.is_active = False
        self.deleted_at = timezone.now()
        self.deletion_reason = reason

        # Remove services
        try:
            self.remove_from_external_services()
        except ValidationError:
            raise ValueError("Enter a valid email address")

        # self.save()

        logger.info(f"User {self.email} soft deleted and Slack account deactivated. Reason: {reason}")

    def restore(self):
        """
        Restore a soft-deleted user account.
        """
        self.is_deleted = False
        self.is_active = True
        self.deleted_at = None
        self.deletion_reason = None

        # Reactivate Slack account
        if self.slack_user_id:
            send_invite(self.email)

        logger.info(f"User {self.email} restored and Slack account reactivated")

        self.save()

    def remove_from_external_services(self):
        """
        Remove the user from external services like Slack and ConvertKit.
        """
        try:
            # Implement Slack removal
            # Deactivate Slack account
            if self.slack_user_id:
                slack_user_id = deactivate_slack_user(self.email, self.slack_user_id)
            else:
                slack_user_id = deactivate_slack_user(self.email)

            if slack_user_id:
                self.slack_user_id = slack_user_id

            self.save()
            logger.info(f"User {self.email} removed from Slack")
        except Exception as e:
            logger.error(f"Failed to remove user {self.email} from Slack: {str(e)}")

        # Implement ConvertKit removal
        removed_email = remove_user_from_convertkit(self.email)
        if removed_email:
            logger.info(f"User {self.email} removed from ConvertKit")
            return True
        else:
            logger.error(f"Failed to remove user {self.email} from ConvertKit: {str(e)}")
            return False

    def has_module_perms(self, app_label):
        """
        Returns True if the user has any permissions in the given app label.
        """
        # User has the named permission from the app label.
        return (
                self.is_staff
                or self.user_permissions.filter(content_type__app_label=app_label).exists()
                or self.is_superuser
        )

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission.
        """
        return self.is_active and (
                self.is_superuser or self.user_permissions.filter(codename=perm).exists()
        )


class UserVerificationToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def is_expired(self):
        return self.created_at < (datetime.datetime.now() - datetime.timedelta(days=1))


class SexualIdentities(models.Model):
    name = models.CharField(max_length=30, null=False, unique=True)
    normalized_name = models.CharField(null=True, blank=True, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class GenderIdentities(models.Model):
    name = models.CharField(max_length=30, null=False, unique=True)
    normalized_name = models.CharField(null=True, blank=True, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EthicIdentities(models.Model):
    name = models.CharField(max_length=30, null=False, unique=True)
    normalized_name = models.CharField(null=True, blank=True, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class PronounsIdentities(models.Model):
    name = models.CharField(max_length=30, null=False, unique=True)
    normalized_name = models.CharField(null=True, blank=True, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class CommunityNeeds(models.Model):
    name = models.CharField(null=False, blank=False, max_length=300)
    normalized_name = models.CharField(null=True, blank=True, max_length=300)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name


class MembersSpotlight(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    notes = models.CharField(max_length=140, null=False)
    blog_link = models.URLField(max_length=200, null=False)
    is_email_sent = models.BooleanField(default=False)
    is_social_media_sent = models.BooleanField(default=False)
    twitter_post = QuillField(max_length=280, null=True, blank=True)
    facebook_post = QuillField(max_length=280, null=True, blank=True)
    ig_post = QuillField(max_length=280, null=True, blank=True)
    linkedin_post = QuillField(max_length=280, null=True, blank=True)
    profile_url = models.URLField(max_length=200)
    social_img_url = models.URLField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.user.first_name + " spotlight"


class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    photo = models.FileField(null=True, blank=True, upload_to="users", max_length=400)
    # timezone = models.CharField(max_length=50, choices=[(tz, tz) for tz in pytz.all_timezones])
    access_token = models.CharField(max_length=255, null=True)
    # Marketing
    marketing_monthly_newsletter = models.BooleanField(
        blank=False, null=False, default=False
    )
    marketing_events = models.BooleanField(blank=False, null=False, default=False)
    marketing_identity_based_programing = models.BooleanField(
        blank=False, null=False, default=False
    )
    marketing_jobs = models.BooleanField(blank=False, null=False, default=False)
    marketing_org_updates = models.BooleanField(blank=False, null=False, default=False)
    # terms
    is_permissions_agree = models.BooleanField(default=False, blank=True, null=True)
    is_coc_agree = models.BooleanField(default=False, blank=True, null=True)
    is_media_agree = models.BooleanField(default=False, blank=True, null=True)
    is_privacy_agree = models.BooleanField(default=False, blank=True, null=True)
    is_terms_agree = models.BooleanField(default=False, blank=True, null=True)
    # social links
    linkedin = models.URLField(null=True, blank=True, max_length=200)
    instagram = models.CharField(null=True, blank=True, max_length=200)
    github = models.URLField(null=True, blank=True, max_length=200)
    twitter = models.CharField(null=True, blank=True, max_length=200)
    youtube = models.URLField(null=True, blank=True, max_length=200)
    personal = models.URLField(null=True, blank=True, max_length=200)

    # DEI Stuff
    identity_sexuality = models.ManyToManyField(SexualIdentities, blank=True,
                                                related_name='userprofile_identity_sexuality')
    is_identity_sexuality_displayed = models.BooleanField(default=False)
    identity_gender = models.ManyToManyField(GenderIdentities, blank=True, related_name='userprofile_identity_gender')
    is_identity_gender_displayed = models.BooleanField(default=False)
    identity_ethic = models.ManyToManyField(EthicIdentities, blank=True, related_name='userprofile_identity_ethic')
    is_identity_ethic_displayed = models.BooleanField(default=False)
    identity_pronouns = models.ManyToManyField(PronounsIdentities, blank=True,
                                               related_name='userprofile_identity_pronouns')
    is_pronouns_displayed = models.BooleanField(default=False)
    disability = models.BooleanField(blank=True, null=True, choices=CHOICES)
    is_disability_displayed = models.BooleanField(default=False)
    care_giver = models.BooleanField(blank=True, null=True, choices=CHOICES)
    is_care_giver_displayed = models.BooleanField(default=False)
    VETERAN_STATUS = (
        ("1", "I am not a protected veteran"),
        (
            "2",
            "I identify as one or more of the classifications of a protected veteran",
        ),
        ("3", "Prefer not to answer"),
    )
    veteran_status = models.CharField(
        max_length=100, choices=VETERAN_STATUS, blank=True, null=True
    )
    is_veteran_status_displayed = models.BooleanField(default=False)
    HOW_CONNECTION_MADE = (
        ("twitter", "Twitter"),
        ("facebook", "Facebook"),
        ("linkedin", "LinkedIn"),
        ("instagram", "Instagram"),
        ("slack", "Slack"),
        ("youtube", "Youtube"),
        ("github", "Github"),
        ("clubhouse", "Clubhouse"),
        ("other", "Other"),
    )
    how_connection_made = models.CharField(
        max_length=9, choices=HOW_CONNECTION_MADE, blank=True, null=True
    )
    TBC_INTEREST = (
        ("Job Placement Help", "Job Placement Help"),
        ("Mentorship", "Mentorship"),
        ("Learning New Skills", "Learning New Skills"),
        ("Help Starting a Business", "Help Starting a Business"),
        (
            "Being a Part of a Welcoming Community",
            "Being a Part of a Welcoming Community",
        ),
        ("Our Paid Open Source Program", "Our Paid Open Source Program"),
        ("Not Sure at the Moment", "Not Sure at the Moment"),
    )
    tbc_program_interest = models.ManyToManyField(CommunityNeeds)
    # location based info
    location = models.CharField(blank=True, null=True, max_length=200)
    state = models.CharField(blank=True, null=True, max_length=200)
    city = models.CharField(blank=True, null=True, max_length=200)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    is_current_member_spotlight = models.BooleanField(default=False)
    member_spotlight = models.ManyToManyField(MembersSpotlight, blank=True)

    def __str__(self):
        return self.user.first_name + " Profile"

    def get_tbc_program_interest(self):
        """Returns the list of interests."""
        if self.tbc_program_interest:
            return json.loads(self.tbc_program_interest)
        return []

    def set_tbc_program_interest(self, interests):
        """Saves the list of interests as a JSON string."""
        interest_obj = CommunityNeeds.objects.get(name=interests)
        if interests:
            self.tbc_program_interest.add(interest_obj)
        else:
            self.tbc_program_interest = None


class EmailTags(models.Model):
    name = models.CharField(null=False, blank=False, max_length=300)
    type = models.CharField(null=True, blank=True, max_length=300)
    convert_tag_kit_id = models.IntegerField(null=False, blank=False)
    description = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True, null=True, blank=True)

    def __str__(self):
        return self.name
