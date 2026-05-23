from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.utils import timezone

class RegistrationManager(BaseUserManager):

    def create_user(self, mobile_number, name, password=None, role="user"):

        if not mobile_number:
            raise ValueError("Users must have a mobile number")

        user = self.model(
            mobile_number=mobile_number,
            name=name,
            role=role
        )

        user.set_password(password)

        user.save(using=self._db)

        return user


class Registration(AbstractBaseUser):

    ROLE_CHOICES = (
        ("admin", "Admin"),
        ("user", "User"),
    )

    user_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True
    )

    name = models.CharField(max_length=100)

    mobile_number = models.CharField(
        max_length=15,
        unique=True
    )

    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        default="user"
    )

    is_active = models.BooleanField(default=True)

    objects = RegistrationManager()

    USERNAME_FIELD = "mobile_number"

    REQUIRED_FIELDS = ["name"]

    def save(self, *args, **kwargs):

        if not self.user_id:

            last_user = Registration.objects.all().order_by("id").last()

            if last_user:

                try:
                    last_id = int(last_user.user_id.split("-")[1])

                except (IndexError, ValueError):
                    last_id = 0

                new_id = last_id + 1

            else:
                new_id = 1

            self.user_id = f"USER-{new_id:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class PhoneOTP(models.Model):

    id = models.AutoField(primary_key=True)

    phone_number = models.CharField(
        max_length=15,
        unique=True
    )

    otp_code = models.CharField(
        max_length=6,
        null=True,
        blank=True
    )

    is_verified = models.BooleanField(default=False)

    created_by_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    updated_by_name = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):

        return f"{self.phone_number} - OTP: {self.otp_code}"
    

# PLACE MODEL
class Place(models.Model):

    place_name = models.CharField(max_length=200)

    rating = models.FloatField()

    one_person_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    number_of_days_stay = models.IntegerField()

    image = models.ImageField(
        upload_to="places/"
    )

    description = models.TextField()
    booking_date = models.DateTimeField(blank=True, null=True)
    booking_time = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.place_name


# HOTEL MODEL
class Hotel(models.Model):

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE,
        related_name="hotels"
    )

    hotel_name = models.CharField(max_length=200)

    hotel_rating = models.FloatField()

    hotel_price = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    hotel_image = models.ImageField(
        upload_to="hotels/"
    )

    hotel_description = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.hotel_name
    

class Feedback(models.Model):

    user_id = models.CharField(max_length=20)

    feedback = models.TextField()

    is_valid = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):

        return self.user_id

# BOOKING MODEL
class Booking(models.Model):

    user_id = models.ForeignKey(
        Registration,
        to_field="user_id",
        on_delete=models.CASCADE,
        related_name="bookings"
    )

    place = models.ForeignKey(
        Place,
        on_delete=models.CASCADE
    )

    hotel = models.ForeignKey(
        Hotel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    person_name = models.CharField(max_length=200)
    total_price = models.CharField(max_length=200)
    identity_document = models.ImageField(
        upload_to="identity_documents/",blank=True, null=True
    )

    total_people = models.IntegerField(default=1)
    status = models.CharField(max_length=20, default="pending")
    date_of_booking = models.DateTimeField(blank=True, null=True)
    def __str__(self):

        return f"{self.person_name} - {self.place.place_name}"


# BOOKING MEMBERS MODEL
class BookingMember(models.Model):

    booking = models.ForeignKey(
        Booking,
        on_delete=models.CASCADE,
        related_name="members"
    )

    member_name = models.CharField(max_length=200)

    aadhaar_number = models.CharField(max_length=12)

    def __str__(self):

        return self.member_name