from django.urls import path
from .views import (
    FeedbackAPIView,
    FeedbackDetailAPIView,
    RegisterUser,
    SendOTP,
    VerifyOTP,
    LoginUser,
    RefreshTokenAPI,
    UserCount,
    PlaceAPIView,
    PlaceDetailAPIView,
    HotelAPIView,
    HotelDetailAPIView,
)

urlpatterns = [
    path('register/', RegisterUser.as_view()),    
    path('send-otp/', SendOTP.as_view()),
    path('verify-otp/', VerifyOTP.as_view()),
    path('login/', LoginUser.as_view()),
    path('refresh-token/', RefreshTokenAPI.as_view()),
    path('user-count/', UserCount.as_view()),
     # PLACE APIs
    path("places/", PlaceAPIView.as_view()),
    path("places/<int:pk>/", PlaceDetailAPIView.as_view()),
    # HOTEL APIs
    path("hotels/", HotelAPIView.as_view()),
    path("hotels/<int:pk>/", HotelDetailAPIView.as_view()),
    # Feedback API
    path("feedback/", FeedbackAPIView.as_view()),
    path("feedback/<int:pk>/", FeedbackDetailAPIView.as_view()),


]