# -*- coding: utf-8 -*-

from datetime import datetime
from django.db import models
from django.conf import settings
from django.utils import timezone


class OAuth2Token(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=40)
    token_type = models.CharField(max_length=20)
    access_token = models.CharField(max_length=200)
    refresh_token = models.CharField(max_length=200)
    expires_at = models.DateTimeField()

    @classmethod
    def create_from_response(cls, user, app, token):
        expires_at = token['expires_at']
        cls.objects.filter(user=user, name=app).delete()
        cls.objects.create(
            user=user,
            name=app,
            token_type=token['token_type'],
            access_token=token['access_token'],
            refresh_token=token.get('refresh_token'),
            expires_at=datetime.utcfromtimestamp(expires_at),
        )

    def update(self, token):
        self.access_token = token['access_token']
        self.refresh_token = token.get('refresh_token')
        self.expires_at = datetime.utcfromtimestamp(token['expires_at'])
        self.save()

    def to_token(self):
        now = timezone.now()
        diff = (self.expires_at - now)
        return dict(
            access_token=self.access_token,
            token_type=self.token_type,
            refresh_token=self.refresh_token,
            expires_at=datetime.timestamp(self.expires_at),
        )
