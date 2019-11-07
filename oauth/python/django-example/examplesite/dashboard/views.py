# -*- coding: utf-8 -*-

from django.conf import settings
from django.contrib.auth import authenticate, login as django_login, logout as django_logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, reverse, HttpResponse, redirect

from requests_oauthlib import OAuth2Session
import requests

from .models import OAuth2Token


def get_oauth_session(request):
    token = OAuth2Token.objects.filter(
        user=request.user,
        name='wisealpha'
    ).first()
    client_id = settings.OAUTH_SETTINGS['client_id']
    
    if not token:
        redirect_uri = request.build_absolute_uri('/authorize')
        session = OAuth2Session(client_id, redirect_uri=redirect_uri, scope='read_investments')
        authorization_url, state = session.authorization_url(settings.OAUTH_SETTINGS['authorize_url'])
        return None, authorization_url

    def token_updater(new_token):
        token.update(new_token)
    
    refresh_kwargs = {
        'client_id': client_id,
        'client_secret': settings.OAUTH_SETTINGS['client_secret'],
    }
    
    oauth = OAuth2Session(
        client_id,
        token=token.to_token(),
        auto_refresh_kwargs=refresh_kwargs,
        auto_refresh_url=settings.OAUTH_SETTINGS['refresh_token_url'],
        token_updater=token_updater)

    return oauth, None


@login_required
def index(request):
    oauth, authorize_url = get_oauth_session(request)
    if authorize_url:
        return redirect(authorize_url)

    api_url = settings.OAUTH_SETTINGS['api_base_url']
    response = oauth.get(f'{api_url}customers/me/investment-accounts/')
    investment_accounts_response = response.json().get('results')
    investment_accounts = []

    for investment_account in investment_accounts_response:
        reference = investment_account['reference']
        
        balances_response = oauth.get(f'{api_url}customers/me/investment-accounts/{reference}/balances/') 
        wallets = []
        for balance in balances_response.json():
            currency = balance['currency']
            amount = balance['amount']
            wallets.append(f'{currency}{amount}')

        summary_response = oauth.get(f'{api_url}customers/me/investment-accounts/{reference}/products/summary/')
        portfolio_values = []
        summaries = summary_response.json()
        for summary in summaries:
            open_summary = summary['summaries']['open']
            currency = summary['currency']
            portfolio_value = open_summary['portfolio_value']
            portfolio_values.append(f'{currency}{portfolio_value}')

        investment_accounts.append({
            'reference': reference,
            'account_type': investment_account['account_type'],
            'portfolio_values': portfolio_values,
            'wallets': wallets,
        })
    
    return render(request, 'dashboard/index.html', {
        'page': 'index',
        'investment_accounts': investment_accounts,
    })


def login(request):
    if request.user.is_authenticated:
        return redirect(reverse('index'))
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(username=email, password=password)
        if user is not None and user.is_active:
            django_login(request, user)
            return redirect(reverse('index'))
    
    return render(request, 'dashboard/login.html', {
        'page': 'login',
    })


def logout(request):
    django_logout(request)
    return redirect(reverse('login'))


def register(request):
    if request.user.is_authenticated:
        return redirect(reverse('index'))
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = User(username=email)
        user.set_password(password)
        user.save()
        
        user = authenticate(username=email, password=password)
        django_login(request, user)
        return redirect(reverse('index'))
    
    return render(request, 'dashboard/register.html', {
        'page': 'register',
    })


def authorize(request):
    error = request.GET.get('error')
    if error:
        return render(request, 'dashboard/error.html', {
            'error': error,
        })  
    client_id = settings.OAUTH_SETTINGS['client_id']
    oauth = OAuth2Session(client_id)
    token = oauth.fetch_token(
        settings.OAUTH_SETTINGS['access_token_url'],
        client_secret=settings.OAUTH_SETTINGS['client_secret'],
        code=request.GET.get('code'))
    OAuth2Token.create_from_response(request.user, 'wisealpha', token)
    return redirect(reverse('index'))
