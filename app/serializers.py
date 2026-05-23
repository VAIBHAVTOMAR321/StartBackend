import json

from rest_framework import serializers
from .models import Booking, BookingMember, Feedback, Registration, PhoneOTP, Place, Hotel


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

class BookingMemberSerializer(serializers.ModelSerializer):

    class Meta:
        model = BookingMember
        fields = [
            "id",
            "member_name",
            "aadhaar_number"
        ]


class BookingSerializer(serializers.ModelSerializer):

    members = BookingMemberSerializer(
        many=True,
        required=False
    )

    class Meta:

        model = Booking

        fields = [
            "id",
            "user_id",
            "place",
            "hotel",
            "person_name",
            "identity_document",
            "total_people",
            "total_price",
            "booking_date",
            "members"
        ]


    def to_internal_value(self, data):

        # IMPORTANT FIX
        data = data.dict()

        members = data.get("members")

        if members and isinstance(members, str):

            try:
                data["members"] = json.loads(members)

            except Exception:

                raise serializers.ValidationError({
                    "members": "Invalid JSON format"
                })

        return super().to_internal_value(data)


    def create(self, validated_data):

        members_data = validated_data.pop("members", [])

        booking = Booking.objects.create(**validated_data)

        for member in members_data:

            BookingMember.objects.create(
                booking=booking,
                **member
            )

        return booking

    def update(self, instance, validated_data):

        members_data = validated_data.pop(
            "members",
            None
        )

        instance.user_id = validated_data.get(
            "user_id",
            instance.user_id
        )

        instance.place = validated_data.get(
            "place",
            instance.place
        )

        instance.hotel = validated_data.get(
            "hotel",
            instance.hotel
        )

        instance.person_name = validated_data.get(
            "person_name",
            instance.person_name
        )

        instance.identity_document = validated_data.get(
            "identity_document",
            instance.identity_document
        )

        instance.total_people = validated_data.get(
            "total_people",
            instance.total_people
        )

        instance.total_price = validated_data.get(
            "total_price",
            instance.total_price
        )

        instance.save()

        if members_data is not None:

            instance.members.all().delete()

            for member in members_data:

                BookingMember.objects.create(
                    booking=instance,
                    **member
                )

        return instance