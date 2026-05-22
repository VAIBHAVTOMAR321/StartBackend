from shlex import quote
from django.utils import timezone
import random
import requests
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.authentication import JWTAuthentication
from app.permissions import IsAdminUserCustom

from .models import Feedback, PhoneOTP, Registration,Place, Hotel
from .serializers import (
    RegisterUserSerializer,
    LoginUserSerializer,
    SendOTPSerializer,
    UserGetSerializer,
    VerifyOTPSerializer,
    RefreshTokenSerializer,
    PlaceSerializer,
    HotelSerializer,
    FeedbackSerializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from django.contrib.auth.hashers import check_password


# ================= REGISTER USER =================
class RegisterUser(APIView):

    

    # GET ALL USERS
    def get(self, request):

        users = Registration.objects.all().order_by("-id")

        serializer = UserGetSerializer(
            users,
            many=True
        )

        return Response({
            "status": True,
            "message": "Users fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # REGISTER USER
    def post(self, request):

        serializer = RegisterUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            name = serializer.validated_data["name"]
            mobile_number = serializer.validated_data["mobile_number"]
            password = serializer.validated_data["password"]

            # Prevent admin registration
            if mobile_number == "9999999999":
                return Response({
                    "status": False,
                    "message": "This number is reserved for admin"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check OTP verification
            try:
                otp_entry = PhoneOTP.objects.get(
                    phone_number=mobile_number
                )

                if not otp_entry.is_verified:
                    return Response({
                        "status": False,
                        "message": "Please verify OTP first"
                    }, status=status.HTTP_400_BAD_REQUEST)

            except PhoneOTP.DoesNotExist:
                return Response({
                    "status": False,
                    "message": "OTP not sent"
                }, status=status.HTTP_404_NOT_FOUND)

            # Check existing user
            if Registration.objects.filter(
                mobile_number=mobile_number
            ).exists():

                return Response({
                    "status": False,
                    "message": "Mobile number already registered"
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create user
            user = Registration.objects.create_user(
                mobile_number=mobile_number,
                name=name,
                password=password,
                role="user"
            )

            # Reset OTP
            otp_entry.is_verified = False
            otp_entry.save()

            return Response({
                "status": True,
                "message": "Registration Successful",
                "user_id": user.user_id,
                "role": user.role
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
# ================= USER COUNT =================
class UserCount(APIView):
    
    def get(self, request):

        user_count = Registration.objects.count()

        return Response({
            "status": True,
            "user_count": user_count
        }, status=status.HTTP_200_OK)


# ================= SEND OTP =================
class SendOTP(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = SendOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data["phone"]

        try:
            # Generate OTP
            otp = str(random.randint(100000, 999999))

            message = f"Your onetime OTP is {otp} Regards-ICDS Technical"

            encoded_message = quote(message)

            # SMS API URL
            url = (
                f"http://bulksms.saakshisoftware.com/api/mt/SendSMS"
                f"?user=Brainrock"
                f"&password=123456"
                f"&senderid=BCSINF"
                f"&channel=trans"
                f"&DCS=0"
                f"&flashsms=0"
                f"&number={phone}"
                f"&text={encoded_message}"
                f"&route=04"
                f"&DLTTemplateId=1207163827265054435"
                f"&PEID=1201163222226675668"
            )

            response = requests.get(url, timeout=30)

            if response.status_code == 200:

                # Update or Create OTP
                PhoneOTP.objects.update_or_create(
                    phone_number=phone,
                    defaults={
                        "otp_code": otp,
                        "is_verified": False,
                        "created_at": timezone.now()
                    }
                )

                return Response({
                    "success": True,
                    "message": "OTP sent successfully"
                }, status=status.HTTP_200_OK)

            return Response({
                "success": False,
                "message": "SMS gateway error"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ================= VERIFY OTP =================
class VerifyOTP(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = VerifyOTPSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "success": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        phone = serializer.validated_data["phone"]
        otp = serializer.validated_data["otp"]

        try:
            otp_entry = PhoneOTP.objects.get(phone_number=phone)

            if otp_entry.otp_code == otp:

                otp_entry.is_verified = True
                otp_entry.save()

                return Response({
                    "success": True,
                    "message": "OTP verified successfully"
                }, status=status.HTTP_200_OK)

            return Response({
                "success": False,
                "message": "Invalid OTP"
            }, status=status.HTTP_400_BAD_REQUEST)

        except PhoneOTP.DoesNotExist:
            return Response({
                "success": False,
                "message": "Phone number not found"
            }, status=status.HTTP_404_NOT_FOUND)


# ================= LOGIN USER =================
class LoginUser(APIView):

    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = LoginUserSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        mobile_number = serializer.validated_data["mobile_number"]
        password = serializer.validated_data["password"]

        try:

            # ================= ADMIN LOGIN =================
            if (
                mobile_number == "9999999999"
                and password == "admin@123"
            ):

                admin_user, created = Registration.objects.get_or_create(
                    mobile_number="9999999999",
                    defaults={
                        "name": "Admin",
                        "role": "admin",
                        "is_staff": True,
                        "is_superuser": True,
                    }
                )

                # Set password if not already set
                admin_user.set_password("admin@123")
                admin_user.save()

                refresh = RefreshToken.for_user(admin_user)

                return Response({
                    "status": True,
                    "message": "Admin Login Successful",

                    "user_id": admin_user.user_id,

                    "role": admin_user.role,

                    "access_token": str(refresh.access_token),

                    "refresh_token": str(refresh)

                }, status=status.HTTP_200_OK)

            # ================= NORMAL USER LOGIN =================
            user = Registration.objects.get(
                mobile_number=mobile_number
            )

            if check_password(password, user.password):

                refresh = RefreshToken.for_user(user)

                return Response({
                    "status": True,
                    "message": "Login Successful",

                    "user_id": user.user_id,

                    "role": user.role,

                    "access_token": str(refresh.access_token),

                    "refresh_token": str(refresh)

                }, status=status.HTTP_200_OK)

            return Response({
                "status": False,
                "message": "Invalid Password"
            }, status=status.HTTP_400_BAD_REQUEST)

        except Registration.DoesNotExist:

            return Response({
                "status": False,
                "message": "User not found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:

            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# ================= REFRESH TOKEN =================
class RefreshTokenAPI(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):

        serializer = RefreshTokenSerializer(data=request.data)

        if not serializer.is_valid():
            return Response({
                "status": False,
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

        refresh_token = serializer.validated_data["refresh_token"]

        try:
            refresh = RefreshToken(refresh_token)

            return Response({
                "status": True,
                "access_token": str(refresh.access_token)
            }, status=status.HTTP_200_OK)

        except TokenError as e:

            error_message = str(e)

            if "expired" in error_message.lower():
                return Response({
                    "status": False,
                    "message": "Refresh token expired"
                }, status=status.HTTP_401_UNAUTHORIZED)

            return Response({
                "status": False,
                "message": "Invalid refresh token"
            }, status=status.HTTP_401_UNAUTHORIZED)

        except Exception as e:
            return Response({
                "status": False,
                "message": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class PlaceAPIView(APIView):

    # GET FOR ALL USERS & ADMIN
    authentication_classes = []
    permission_classes = []

    def get(self, request):

        places = Place.objects.all().order_by("-id")

        serializer = PlaceSerializer(
            places,
            many=True
        )

        return Response({
            "status": True,
            "message": "Places fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ONLY ADMIN CAN ADD PLACE
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUserCustom]

    def post(self, request):

        serializer = PlaceSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Place added successfully"
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# PLACE PUT & DELETE
class PlaceDetailAPIView(APIView):

    # ONLY ADMIN
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAdminUserCustom]

    def get_object(self, pk):

        try:
            return Place.objects.get(id=pk)

        except Place.DoesNotExist:
            return None

    # UPDATE PLACE
    def put(self, request, pk):

        place = self.get_object(pk)

        if not place:
            return Response({
                "status": False,
                "message": "Place not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = PlaceSerializer(
            place,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Place updated successfully"
            })

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # DELETE PLACE
    def delete(self, request, pk):

        place = self.get_object(pk)

        if not place:
            return Response({
                "status": False,
                "message": "Place not found"
            }, status=status.HTTP_404_NOT_FOUND)

        place.delete()

        return Response({
            "status": True,
            "message": "Place deleted successfully"
        })

# HOTEL POST & GET
class HotelAPIView(APIView):

    # GET ALL HOTELS
    def get(self, request):

        hotels = Hotel.objects.all().order_by("-id")

        serializer = HotelSerializer(
            hotels,
            many=True
        )

        return Response({
            "status": True,
            "message": "Hotels fetched successfully",
            "data": serializer.data
        })

    # ADD HOTEL
    def post(self, request):

        serializer = HotelSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Hotel added successfully"
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# HOTEL PUT & DELETE
class HotelDetailAPIView(APIView):

    def get_object(self, pk):

        try:
            return Hotel.objects.get(id=pk)

        except Hotel.DoesNotExist:
            return None

    # UPDATE HOTEL
    def put(self, request, pk):

        hotel = self.get_object(pk)

        if not hotel:
            return Response({
                "status": False,
                "message": "Hotel not found"
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = HotelSerializer(
            hotel,
            data=request.data,
            partial=True
        )

        if serializer.is_valid():

            serializer.save()

            return Response({
                "status": True,
                "message": "Hotel updated successfully"
            })

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    # DELETE HOTEL
    def delete(self, request, pk):

        hotel = self.get_object(pk)

        if not hotel:
            return Response({
                "status": False,
                "message": "Hotel not found"
            }, status=status.HTTP_404_NOT_FOUND)

        hotel.delete()

        return Response({
            "status": True,
            "message": "Hotel deleted successfully"
        })
    
# ================= FEEDBACK APIs =================

class FeedbackAPIView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    # GET ALL FEEDBACK
    def get(self, request):

        feedbacks = Feedback.objects.all().order_by("-id")

        serializer = FeedbackSerializer(
            feedbacks,
            many=True
        )

        return Response({
            "status": True,
            "message": "Feedback fetched successfully",
            "data": serializer.data
        }, status=status.HTTP_200_OK)

    # ONLY USER CAN SEND FEEDBACK
    def post(self, request):

        if request.user.role != "user":

            return Response({
                "status": False,
                "message": "Only users can send feedback"
            }, status=status.HTTP_403_FORBIDDEN)

        serializer = FeedbackSerializer(data=request.data)

        if serializer.is_valid():

            serializer.save(
                is_valid=False
            )

            return Response({
                "status": True,
                "message": "Feedback sent successfully"
            }, status=status.HTTP_201_CREATED)

        return Response({
            "status": False,
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


# UPDATE & DELETE FEEDBACK
class FeedbackDetailAPIView(APIView):

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):

        try:
            return Feedback.objects.get(id=pk)

        except Feedback.DoesNotExist:
            return None

    # ONLY ADMIN CAN UPDATE is_valid
    def put(self, request, pk):

        if request.user.role != "admin":

            return Response({
                "status": False,
                "message": "Only admin can update feedback"
            }, status=status.HTTP_403_FORBIDDEN)

        feedback = self.get_object(pk)

        if not feedback:

            return Response({
                "status": False,
                "message": "Feedback not found"
            }, status=status.HTTP_404_NOT_FOUND)

        feedback.is_valid = request.data.get(
            "is_valid",
            feedback.is_valid
        )

        feedback.save()

        return Response({
            "status": True,
            "message": "Feedback updated successfully"
        }, status=status.HTTP_200_OK)

    # ONLY ADMIN CAN DELETE
    def delete(self, request, pk):

        if request.user.role != "admin":

            return Response({
                "status": False,
                "message": "Only admin can delete feedback"
            }, status=status.HTTP_403_FORBIDDEN)

        feedback = self.get_object(pk)

        if not feedback:

            return Response({
                "status": False,
                "message": "Feedback not found"
            }, status=status.HTTP_404_NOT_FOUND)

        feedback.delete()

        return Response({
            "status": True,
            "message": "Feedback deleted successfully"
        }, status=status.HTTP_200_OK)