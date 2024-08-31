"""
URL configuration for chatbot project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.urls import path

from . import views

handler404 = views.custom_404

urlpatterns = [
    path('', views.index,name="index"),
    path('chat/<str:track_id>', views.chat,name="chat"),
    path('genrate-new-chat/', views.genrate_new_chat, name="genrate-new-chat"),
    path('chat-bot/<str:track_id>', views.chat_bot,name="chat-bot"),
    path('genrate-new-chat-bot/', views.genrate_new_chat_bot, name="genrate-new-chat-bot"),
    path('upload-document/', views.upload_document,name="upload-document"),
    # authentication urls
    path('login_page/', views.login_page,name="login_page"),
    path("check-email/", views.check_email, name="check_email"),
    path("signup_page/", views.signup_page, name="signup_page"),
    path("forget_password/", views.forget_password, name="forget_password"),
    path("change_password/", views.change_password, name="change_password"),
    path("change_password_page/<token>/",views.change_password_page,name="change_password_page"),
    path("update-password/", views.update_password, name="update-password"), # change password from Account setting
    # dasboard
    path("dashboard/", views.dashboard, name="dashboard"),
    path("files/<str:is_sort>/", views.files, name="files"),
    path("integrations/", views.integrations, name="integrations"),
    path('account-setting/', views.account_setting,name="account-setting"),
    path('subscription/', views.subscription,name="subscription"),
    path("autocomplete/",views.EventAutocomplete.as_view(),name="event-autocomplete"),
    path('filter_document/', views.filter_document, name='filter_document'),
    path('process-selected-files/', views.process_selected_files, name='process_selected_files'),
    path('delete-ai-search-data/<int:id>/<str:document_name>', views.delete_ai_search_data, name="delete-ai-search-data"),
    # xero authentication chatbot
    path('login-with-xero/', views.login_with_xero, name='login-with-xero'),
    path('callback/', views.oauth_callback, name='oauth_callback'),
    path('logout-user/', views.logout_user, name='logout-user'),
    # stripe route
    path('config/', views.stripe_config),
    path('create_checkout_session/', views.create_checkout_session),
    path('success/', views.SuccessView),
    path('cancelled/', views.CancelledView),
    path("cancel-subscription/", views.cancel_subscription, name="cancel_subscription"),
]

