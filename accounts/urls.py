from django.urls import path

from . import views

urlpatterns = [
    path('search', views.UserSearchAPI.as_view(), name='user_search'),
    path('register/<str:phone_or_email>', views.RegisterUserAPI.as_view(), name='user_register'),
    path('regvalidate', views.ValidateSendRegister.as_view(), name='user_validate_register'),
    path('regvalidate_resend/<str:phone_or_email>', views.ValidateResendRegister.as_view(), name='user_validate_register_resend'),
    path('password_reset', views.ResetPasswordValidate.as_view(), name='user_password_reset'),
    path('password_reset_resend/<str:phone_or_email>', views.PasswordResetResendRegister.as_view(), name='user_password_reset_resend'),
    path('password_reset_code/<str:phone_or_email>', views.ResetPasswordCode.as_view(), name='user_password_reset_code'),
    path('password_reset_complete/<str:uuid>', views.ResetPassword.as_view(), name='user_password_reset_complete'),
    path('login', views.LoginAPI.as_view(), name='user_login'),
    path('logout', views.LogoutAPI.as_view(), name='user_logout'),
    path('actions', views.UsersActionsAPI.as_view(), name='user_actions'),
    path('password_change', views.PasswordChangeAPI.as_view(), name='user_password_change'),
    path('me', views.MeDetailAPI.as_view(), name='me_detail'),
    path('detail/<str:username>', views.UserDetailAPI.as_view(), name='user_detail'),
    path('follow/<str:username>/<str:action>', views.UserFollowActionAPI.as_view(), name='user_friend'),
    path('follow-accept/<str:username>', views.UserFollowAcceptAPI.as_view(), name='user_friend_accept'),
    path('follow-list/<str:follow>', views.UserFollowListAPI.as_view(), name='user_follow_list'),
]

