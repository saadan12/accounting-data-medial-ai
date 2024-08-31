from django.shortcuts import render, redirect
from django.urls import reverse
from django.conf import settings
import datetime
from datetime import datetime, timezone
from .models import XeroToken
import logging
from django.contrib.auth.models import User
import jwt
import stripe
import uuid
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.identity import ClientSecretCredential
from azure.mgmt.datafactory import DataFactoryManagementClient
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token
from xero_python.identity import IdentityApi
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.timezone import make_aware
from django.http.response import JsonResponse
from django.contrib.auth import authenticate, login, logout,update_session_auth_hash
from requests_oauthlib import OAuth2Session
from io import BytesIO
import json
from azure.core.exceptions import ResourceNotFoundError
from azure.keyvault.secrets import SecretClient
from chatting.search_document import save_file_to_search, call_large_model
from chatting.connectors import request_to_model
from django.contrib import messages
from chatting.helpers import (
    forget_password_mail,
)
from chatting.models import Profile, Document, XeroChatHistory, DocumetChatHistory
import os
from dotenv import load_dotenv
load_dotenv()

endpoint = os.environ.get("SEARCH_ENDPOINT")
doc_idx = "document_chat"
keys = os.environ.get("SEARCH_KEY")

def delete_ai_search(user_id, document_name):
    key = AzureKeyCredential(keys)
    search_client = SearchClient(endpoint=endpoint, index_name=doc_idx, credential=key)
    results = search_client.search(
        # search_text="*",
        filter=f"user_id eq '{user_id}' and file_name eq '{document_name}'"
    )
    print("results ", results)
    filtered_results = []
    for result in results:
        filtered_result = {}
        filtered_result["ID"] = result.get("ID")
        filtered_results.append(filtered_result)
    if filtered_results:
        try:
            delete_result = search_client.delete_documents(documents=filtered_results)
            print(f"Deletion succeeded: {all(result.succeeded for result in delete_result)}")
            search_client.close()
        except Exception as e:
            print(f"An error occurred: {e}")
    else:
        print("No documents found matching the criteria.")

def is_get_subscription(request):
    try:
        user_profile = Profile.objects.get(user_id=request.user.id)
    except Profile.DoesNotExist:
        user_profile = Profile.objects.create(user_id=request.user.id)
    if not user_profile.is_payment or (
        user_profile.payment_expiration_date
        and user_profile.payment_expiration_date < datetime.now(timezone.utc)
    ):
        messages.error(request, "Please make a payment to post a ticket.")
        return True
    else:
        return False

def delete_ai_search_data(request, id ,document_name):
    delete_ai_search(request.user.id, document_name)
    Document.objects.get(id = id).delete()
    return redirect('genrate-new-chat-bot')

def index(request):
    return render(request, 'landing_page.html')

@csrf_exempt
def login_page(request):
    try:
        if request.user.is_authenticated:
            return redirect('dashboard')
        if request.method == "POST":
            email = request.POST["email"].lower()
            password = request.POST["password"]
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                return redirect('/account/login/')
            else:
                messages.error(request, "Invalid Credentials")
                return render(request, "login.html")
        
        return redirect(reverse('two_factor:login'))
    except Exception as e:
        logging.info(f"Error {e}")
def logout_user(request):
    logout(request)
    return redirect('index')

@csrf_exempt
def signup_page(request):
    if request.method == "POST":
        try:
            password = request.POST["password"]
            confirm_password = request.POST["confirm_password"]
            normal_email = request.POST["email"]
            first_name = request.POST["first_name"]
            last_name = request.POST["last_name"]
            email = normal_email.lower()
            phone = request.POST["phone"]
            # is_payment = False  # Default value for is_payment
            # expiration_date = None  # Default value for expiration_date

            # Get the current datetime
            # current_datetime = datetime.now()
            # Check if the password meets the minimum length requirement
            if len(password) < 8 or len(confirm_password) < 8:
                messages.error(request, "Password Length Minimum 8 Characters")
                return redirect("signup_page")

            # Check if the email already exists in the database
            if User.objects.filter(email=email).exists():
                messages.error(request, "Email address already exists")
                return redirect("signup_page")

            # Check if the passwords match
            if password != confirm_password:
                messages.error(request, "Passwords do not match")
                return redirect("signup_page")

            user = User.objects.create_user(
                username=email,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name,
            )
            Profile.objects.create(
                user=user,
                phone=phone,
                # is_payment=is_payment,
                # payment_expiration_date=expiration_date,
            )

            auth_user = authenticate(request, username=email, password=password)
            if auth_user:
                login(request, auth_user)
                return redirect("genrate-new-chat")
            else:
                messages.error(request, "Failed to authenticate user")
                return redirect("login_page")
        except Exception as e:
            logging.error(f"Error {e}")
    else:
        try:
            if request.user.is_authenticated:
                return redirect("genrate-new-chat")
            return render(
                request,
                "signup.html",
            )
        except Exception as e:
            logging.error(f"Error {e}")

def forget_password(request):
    return render(request, "forget_password.html")

@csrf_exempt
def change_password(request):
    try:
        if request.method == "POST":
            email = request.POST["email"]
            if not User.objects.filter(email=email).first():
                return redirect("signup_page")
            user = User.objects.get(email=email)
            try:
                profile = Profile.objects.get(user=user)
            except Profile.DoesNotExist:
                profile = Profile(user=user)

            token = str(uuid.uuid4())
            # profile = Profile.objects.get(user=user)
            profile.token = token
            profile.save()
            domain = request.build_absolute_uri("/")
            forget_password_mail(domain, user.email, token)
            messages.success(
                request, "Please check your spam email OR Inbox to reset your password."
            )
            return redirect("login_page")
    except Exception as e:
        logging.error(f"Error {e}")

@login_required(login_url="/account/login")
def dashboard(request):
    return render(request, 'dashboard.html')

@login_required(login_url="/account/login")
def files(request, is_sort):
    is_sort = is_sort.lower() == 'true'
    if is_sort:
        documents = Document.objects.filter(user_id = request.user.id).order_by('-created_at')
    else:
        documents = Document.objects.filter(user_id = request.user.id)
    return render(request, 'files.html', {'documents' : documents})

@csrf_exempt
def process_selected_files(request):
    if request.method == 'POST':
        ids = request.POST.getlist('ids[]')
        if not ids:
            return redirect('files', is_sort='Faslse')
        try:
            ids = list(map(int, ids))
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'Invalid ID format'}, status=400)
        for id in ids:
            document = Document.objects.get(id = id)
            delete_ai_search(document.user_id, document.document_name)            
        deleted_count, _ = Document.objects.filter(id__in=ids).delete()
        return redirect('files', is_sort='False')
    return redirect('files', is_sort='False')

@login_required(login_url="/account/login")
def filter_document(request):
    document_name = request.GET.get('document_name')
    if document_name:
        documents = Document.objects.filter(document_name=document_name, user_id = request.user.id)
        return render(request, 'files.html', {'documents' : documents})
    return redirect('files')

class EventAutocomplete(View):
    def get(self, request):
        query = request.GET.get("term", "")
        events = Document.objects.filter(
            user=request.user,
            document_name__icontains=query
        ).values_list('document_name', flat=True)[:10]
        results = [{"label": event_name, "value": event_name} for event_name in events]
        return JsonResponse(results, safe=False)

@login_required(login_url="/account/login")
def integrations(request):
    return render(request, 'integrations.html')

@login_required(login_url="/account/login")
def subscription(request):
    return render(request, 'subscription.html')

@csrf_exempt
def change_password_page(request, token):
    try:
        profile = Profile.objects.get(token=token)
        if request.method == "POST":
            new_password = request.POST["password1"]
            confirm_password = request.POST["password2"]
            user_id = request.POST["user_id"]
            if user_id is None:
                return redirect(
                    reverse("change_password_page", kwargs={"token": token})
                )
            if len(new_password) < 8 or len(confirm_password) < 8:
                messages.success(request, "Password length Should be Eight Digit")
                return redirect(
                    reverse("change_password_page", kwargs={"token": token})
                )
            if new_password != confirm_password:
                messages.success(request, "Password is not Match")
                return redirect(
                    reverse("change_password_page", kwargs={"token": token})
                )
            user = User.objects.get(id=user_id)
            user.username = user.email
            user.set_password(new_password)
            user.save()
            messages.success(request, "Password has been changed")
            return redirect("login_page")
        return render(request, "change_password.html", {"user_id": profile.user.id})
    except ObjectDoesNotExist:
        messages.error(request, "Profile not found or token is invalid")
        return redirect("login_page")
    except Exception as e:
        logging.error(f"Error {e}")

def check_email(request):
    if request.method == "POST":
        normal_email = request.POST.get("email").lower()
        email_exists = User.objects.filter(email=normal_email).exists()
        return JsonResponse({"exists": email_exists})

# Initialize the ApiClient
api_client = ApiClient(
    Configuration(
        debug=settings.DEBUG,
        oauth2_token=OAuth2Token(
            client_id=settings.CLIENT_ID, client_secret=settings.CLIENT_SECRET
        ),
    ),
    pool_threads=1,
)
# Define the OAuth2Session
oauth = OAuth2Session(
    client_id=settings.CLIENT_ID,
    redirect_uri=settings.REDIRECT_URI,
    scope=settings.SCOPE,
)

def custom_404(request, *args, **kwargs):
    return render(request, "404.html", status=404)

@login_required(login_url="/account/login")
def chat_bot(request,track_id = None):
    if is_get_subscription(request):
        return redirect('subscription')
    if request.method == "POST":
        query = request.POST['query']
        ai_result = call_large_model(query, request.user.id)
        DocumetChatHistory.objects.create(user_id = request.user.id,question = query, ai_result= ai_result,track_chat_id = track_id )
        return redirect('chat-bot', track_id = track_id )
    documents = Document.objects.filter(user_id = request.user.id)
    chat_histories = DocumetChatHistory.objects.filter(user_id = request.user.id,track_chat_id = track_id).order_by('created_at')
    unique_track_ids = DocumetChatHistory.objects.filter(user_id=request.user.id).values_list('track_chat_id', flat=True).distinct().order_by('-created_at')
    unique_items = unique_preserving_order(unique_track_ids)
    return render(request, 'chat_bot.html',{'chat_histories' : chat_histories, 'documents' : documents, 'unique_track_ids' : unique_items, 'active_track_id' : track_id, 'chat_redirect' : 'chat-bot'})

@login_required(login_url="/account/login")
def update_password(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        user = request.user
        if new_password != confirm_password:
            messages.error(request, "Password is not Matched")
            return redirect('account-setting')
        if len(new_password) < 8 or len(confirm_password) < 8:
            messages.error(request, "Password length is less than Eight Charater")
            return redirect('account-setting')
        if not user.check_password(current_password):
            messages.error(request, "Current Password is Not Matched")
            return redirect('account-setting')
        if new_password:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)
            return redirect('account-setting')
        return redirect('account-setting')
    return redirect('account-setting')

@login_required(login_url="/account/login")
def account_setting(request):
    if request.method == 'POST':
        try:
            first_name = request.POST.get('first_name', None)
            email = request.POST.get('email', None)
            password = request.POST.get('password', None)
            if first_name:
                User.objects.filter(id=request.user.id).update(first_name=first_name)
                return redirect('account-setting')
            user = request.user
            if not user.check_password(password):
                messages.error(request, "Password is Incorrect")
                return redirect('dashboard')
            if email:
                user.email = email
                user.username = email
                user.save()
                return redirect('account-setting')
            messages.success(request, "Account settings updated!")
            return redirect("genrate-new-chat")
        except Exception as e:
            logging.error("Update Profile View", str(e))
    else:
        try:
            profile, created = Profile.objects.get_or_create(user=request.user)
            return render(request, "account_setting.html", {'profile' : profile})
        except Exception as e:
            logging.error(f"Error at account setting {e}")

def format_bytes(size):
    power = 2**10
    n = 0
    power_labels = {0 : '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return format(size, ".2f")  , power_labels[n]+'B'

@login_required(login_url="/account/login")            
def upload_document(request):
    if request.method == "POST":
        file = request.FILES['filess']
        size , unit= format_bytes(file.size)
        save_file_to_search(file,request.user.id)
        Document.objects.create(user_id = request.user.id, document_name = file.name, file_size = str(size)+str(unit))
        return redirect('genrate-new-chat-bot')

@login_required(login_url="/account/login")
def cancel_subscription(request):
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        user_profile = Profile.objects.get(user=request.user)
        subscriptions = stripe.Subscription.list(
            customer=user_profile.stripe_customer_id
        )
        print(subscriptions.data[0].id)
        stripe.Subscription.delete(subscriptions.data[0].id)
        # stripe.Customer.delete(user_profile.stripe_customer_id)
        # user_profile.stripe_customer_id=None
        user_profile.cancel_subscription = True
        # user_profile.payment_expiration_date=None
        user_profile.save()
        messages.error(request, "Subscription cancelled successfully!")
        return redirect("account-setting")
    except Exception as e:
        print("Subscription cancelled View", str(e))

def genrate_new_chat(request):
    return redirect('chat', track_id = str(uuid.uuid4()))

def genrate_new_chat_bot(request):
    return redirect('chat-bot', track_id = str(uuid.uuid4()))

def unique_preserving_order(items):
    seen = set()
    unique_items = []
    for item in items:
        if item not in seen:
            unique_items.append(item)
            seen.add(item)
    return unique_items

@login_required(login_url="/account/login")
def chat(request,track_id = None):
    if is_get_subscription(request):
        return redirect('subscription')
    if not request.user.profile.is_xero_connection:
        return redirect('integrations')
    bot_response=''
    question=''
    if request.method == 'POST':
        question = request.POST['question']
        bot_response = request_to_model(question,request.user.id)
        XeroChatHistory.objects.create(question = question, user_id = request.user.id, ai_result = bot_response, track_chat_id = track_id)
        return redirect('chat', track_id = track_id )
    xero_chat_histories = XeroChatHistory.objects.filter(user_id = request.user.id, track_chat_id = track_id).order_by('created_at')
    unique_track_ids = XeroChatHistory.objects.filter(user_id=request.user.id).values_list('track_chat_id', flat=True).distinct().order_by('-created_at')
    unique_items = unique_preserving_order(unique_track_ids)
    return render(request,'chat.html',{'xero_chat_histories': xero_chat_histories, 'unique_track_ids' : unique_items, 'active_track_id' : track_id, 'chat_redirect' : 'chat'})

def obtain_xero_oauth2_token(request):
    return request.session.get("token")

def store_xero_oauth2_token(request, token):
    request.session["token"] = token
    request.session.modified = True

def xero_token_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        xero_token = obtain_xero_oauth2_token(request)
        if not xero_token:
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return _wrapped_view

# Initialize the OAuth2 session
oauth = OAuth2Session(settings.CLIENT_ID, redirect_uri=settings.REDIRECT_URI, scope=settings.SCOPE)
def login_with_xero(request):
    authorization_url, state = oauth.authorization_url(settings.AUTHORIZATION_URL)
    request.session['oauth_state'] = state
    return redirect(authorization_url)

def oauth_callback(request):
    state = request.session.get('oauth_state')
    token = oauth.fetch_token(
        settings.ACCESS_TOKEN_URL,
        authorization_response=request.build_absolute_uri(),
        client_secret=settings.CLIENT_SECRET,
        include_client_id=True
    )
    # Decode the token to extract user information
    user_info = jwt.decode(token['id_token'], options={"verify_signature": False})
    store_xero_oauth2_token(request.user, token)
    messages.success(request,"Token saved successfully into Key Vault and Pipeline executed! Please wait for few minutes")
    return redirect('dashboard')

def store_xero_oauth2_token(user, token):
    from django.utils import timezone
    expires_at = timezone.now() + timezone.timedelta(seconds=token['expires_in'])
    xero_token, created = XeroToken.objects.get_or_create(user=user)
    email = user.email
    credential = ClientSecretCredential(
        tenant_id=os.getenv('TENANT_ID'),
        client_id=os.getenv('CLIENT_ID'),
        client_secret=os.getenv('CLIENT_SECRET')
    )
    vault_url = os.getenv('VAULT_URL')
    secret_client = SecretClient(vault_url=vault_url, credential=credential)
    access_token_secret_name = f"{user.id}token"
    token_json = json.dumps({"access_token": token["access_token"], "refresh_token": token["refresh_token"]})
    try:
        secret_client.get_secret(access_token_secret_name)
        secret_client.set_secret(access_token_secret_name, token_json)
    except ResourceNotFoundError:
        secret_client.set_secret(access_token_secret_name, token_json)
        logging.info(f"Created access token for user {user.id}")
    try:

        user.profile.is_xero_connection = True
        user.profile.save()
       
        adf_client = DataFactoryManagementClient(
                credential,
                # subscription
                os.getenv('SUBSCRIPTION_KEY'),
                "https://management.azure.com"
                )
        run_response = adf_client.pipelines.create_run(
                "medial-dev",
                pipeline_name="functions",
                factory_name="medial-datafactory-dev",
                parameters={})
        logging.info(f"{run_response}")
    except Exception as e:
        logging.error(f"{e}")
def logout_xero(request):
    store_xero_oauth2_token(request, None)
    return redirect('dashboard')

@xero_token_required
def export_token(request):
    token = obtain_xero_oauth2_token(request)
    buffer = BytesIO("token={!r}".format(token).encode("utf-8"))
    buffer.seek(0)
    return HttpResponse(
        buffer,
        content_type="application/x-python",
        headers={
            "Content-Disposition": 'attachment; filename="oauth2_token.py"',
        },
    )

@xero_token_required
def refresh_token(request):
    xero_token = obtain_xero_oauth2_token(request)
    new_token = api_client.refresh_oauth2_token()
    return render(request, 'refresh_token.html', {
        'title': 'Xero OAuth2 token',
        'code': json.dumps({"Old Token": xero_token, "New token": new_token}, indent=4),
        'sub_title': 'token refreshed'
    })

def get_xero_tenant_id(request):
    token = obtain_xero_oauth2_token(request)
    if not token:
        return None

    identity_api = IdentityApi(api_client)
    for connection in identity_api.get_connections():
        if connection.tenant_type == "ORGANISATION":
            return connection.tenant_id

@csrf_exempt
def stripe_config(request):
    if request.method == 'GET':
        stripe_config = {'publicKey': settings.STRIPE_PUBLISHABLE_KEY}
        return JsonResponse(stripe_config, safe=False)

@login_required(login_url="/account/login")
@csrf_exempt
def create_checkout_session(request):
    if request.method == 'GET':
        domain_url = request.build_absolute_uri("/")
        stripe.api_key = settings.STRIPE_SECRET_KEY
        try:
            user_profile = Profile.objects.get(user=request.user)
            if not user_profile.stripe_customer_id:
                customer = stripe.Customer.create(
                    email=request.user.email,
                )
                Profile.objects.filter(id=user_profile.id).update(
                    stripe_customer_id=customer.id
                )
            if user_profile.stripe_customer_id:
                    user_profile.stripe_customer_id = user_profile.stripe_customer_id
            if user_profile.free_trail:
                price_id = os.environ.get("PRODUCT_PRICE_ID")
                trial_days = None
            else:
                price_id = os.environ.get("PRODUCT_PRICE_ID")
                trial_days = 7
            user_profile = Profile.objects.get(user=request.user)
            checkout_session = stripe.checkout.Session.create(
                success_url=domain_url + 'success?session_id={CHECKOUT_SESSION_ID}',
                cancel_url=domain_url + 'cancelled/',
                payment_method_types=['card'],
                mode='subscription',
                customer=user_profile.stripe_customer_id,
                line_items=[
                    {
                        'price': os.getenv('PRODUCT_PRICE_ID'),
                        'quantity': 1,
                    }
                ],
                subscription_data={
                    "trial_period_days": trial_days,
                },
            )
            return JsonResponse({'sessionId': checkout_session['id']})
        except Exception as e:
            return JsonResponse({'error': str(e)})
        
@login_required(login_url="/account/login")
def SuccessView(request):
    try:
        stripe.api_key = settings.STRIPE_SECRET_KEY
        user_profile = Profile.objects.get(user=request.user)
        upcoming_invoices = stripe.Invoice.list(
            customer=str(user_profile.stripe_customer_id)
        )
        for invoice in upcoming_invoices["data"]:
            period_end = invoice["lines"]["data"][0]["period"]["end"]
            break
        datetime_obj = datetime.utcfromtimestamp(period_end)
        expiration_date = make_aware(datetime_obj)
        user_profile.is_payment = True
        user_profile.payment_expiration_date = expiration_date
        user_profile.free_trail = True
        user_profile.cancel_subscription = False
        user_profile.save()
        messages.success(request, "Congrats! You have subscribed now")
        return redirect("genrate-new-chat")
    except Exception as e:
        print("Sucess Payment View", str(e))
        
def CancelledView(request):
    return redirect("/")

def check_subscription(user):
    stripe.api_key = settings.STRIPE_SECRET_KEY
    user_profile = Profile.objects.get(user=user)
    if not user_profile.stripe_customer_id and user_profile.is_payment:
        return True
    if user_profile.stripe_customer_id:
        try:
            upcoming_invoices = stripe.Invoice.list(
                customer=str(user_profile.stripe_customer_id)
            )
            for invoice in upcoming_invoices["data"]:
                period_end = invoice["lines"]["data"][0]["period"]["end"]
                print("End of subscription period:", period_end)
                datetime_obj = datetime.utcfromtimestamp(period_end)
                expiration_date = make_aware(datetime_obj)
                print("Convert date and Time ", expiration_date)  # get from the stripe.
                current_date_time = datetime.now(UTC)
                print("Today Date is ", current_date_time)
                if expiration_date < current_date_time:
                    print("Subscription has expired.")
                    user_profile.is_payment = False
                    user_profile.payment_expiration_date = expiration_date
                    user_profile.free_trail = False
                    user_profile.save()
                    return False
                elif expiration_date > current_date_time:
                    print("I have subscription now")
                    user_profile.is_payment = True
                    user_profile.payment_expiration_date = expiration_date
                    user_profile.free_trail = True
                    user_profile.save()
                    return True
            # If no upcoming invoices found
            print("No upcoming invoices found.")
            return True
        except stripe.error.StripeError as e:
            # Handle Stripe API errors
            print("Stripe API error:", str(e))
            return True
    else:
        print("Stripe customer ID not available.")
        return False