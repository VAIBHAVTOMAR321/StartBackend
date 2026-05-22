from rest_framework import serializers
from .models import Feedback, Registration, PhoneOTP, Place, Hotel


# ---------------- REGISTER ----------------
class RegisterUserSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    mobile_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True, min_length=4)

class UserGetSerializer(serializers.ModelSerializer):

    class Meta:
        model = Registration
        fields = [
            "id",
            "user_id",
            "name",
            "mobile_number",
            "role",
            "is_active"
        ]
# ---------------- LOGIN ----------------
class LoginUserSerializer(serializers.Serializer):
    mobile_number = serializers.CharField(max_length=15)
    password = serializers.CharField(write_only=True)


# ---------------- SEND OTP ----------------
class SendOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)

    def validate_phone(self, value):
        if not value.isdigit():
            raise serializers.ValidationError("Phone number must contain digits only")
        return value


# ---------------- VERIFY OTP ----------------
class VerifyOTPSerializer(serializers.Serializer):
    phone = serializers.CharField(max_length=15)
    otp = serializers.CharField(max_length=6)


# ---------------- REFRESH TOKEN ----------------
class RefreshTokenSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()


# ---------------- USER COUNT RESPONSE ----------------
class UserCountSerializer(serializers.Serializer):
    status = serializers.BooleanField()
    user_count = serializers.IntegerField()


# ---------------- REGISTRATION MODEL SERIALIZER ----------------
class RegistrationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Registration
        fields = ["id", "name", "mobile_number"]


# ---------------- PHONE OTP MODEL SERIALIZER ----------------
class PhoneOTPSerializer(serializers.ModelSerializer):

    class Meta:
        model = PhoneOTP
        fields = ["phone_number", "otp_code", "is_verified", "created_at"]

class HotelSerializer(serializers.ModelSerializer):

    class Meta:
        model = Hotel
        fields = "__all__"


class PlaceSerializer(serializers.ModelSerializer):

    hotels = HotelSerializer(
        many=True,
        read_only=True
    )

    class Meta:
        model = Place
        fields = "__all__"


class FeedbackSerializer(serializers.ModelSerializer):

    class Meta:
        model = Feedback

        fields = [
            "id",
            "user_id",
            "feedback",
            "is_valid"
        ]

        read_only_fields = [
            "is_valid"
        ]