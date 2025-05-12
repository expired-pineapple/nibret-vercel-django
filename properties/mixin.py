from math import radians, sin, cos, sqrt, atan2
import uuid
import logging
from django.conf import settings
from django.db import models
from rest_framework.exceptions import ValidationError

class UserLogMixin:
    """
    Enhanced mixin to track user impressions and actions
    Tracks detailed impressions on retrieve actions for logged-in users
    """
    log_message = None

    def _get_action_type(self, request) -> str:
        return self.action_type_mapper().get(request.method.upper(), READ)

    def _build_log_message(self, request) -> str:
        return f"{request.resolver_match.url_name} - {self._get_model_name()}"

    def _get_model_name(self):
        return self.queryset.model._meta.verbose_name.title()

    def get_log_message(self, request) -> str:
        return self.log_message or self._build_log_message(request)

    @staticmethod
    def action_type_mapper():
        return {
            "GET": READ,
            "POST": CREATE,
            "PUT": UPDATE,
            "PATCH": UPDATE,
            "DELETE": DELETE,
        }

    def _write_log(self, request, response):
        status = 'SUCCESS' if response.status_code < 400 else 'FAILED'
        actor = request.user if request.user.is_authenticated else None
        
        if not actor or getattr(settings, "TESTING", False):
            return

        log_data = {
            "actor": actor,
            "action_type": self._get_action_type(request),
            "status": status,
            "remarks": self.get_log_message(request),
        }

        try:
            log_data["content_type"] = ContentType.objects.get_for_model(
                self.queryset.model
            )
            if self.action == 'retrieve':
                log_data["content_object"] = self.get_object()
        except (AttributeError, ValidationError, AssertionError):
            log_data["content_type"] = None

        # Track impressions for successful detail views
        if log_data["action_type"] == READ and self.action == 'retrieve':
            ActivtyLog.objects.create(**log_data)
        # Track other CRUD actions
        elif log_data["action_type"] != READ:
            ActivtyLog.objects.create(**log_data)

    def finalize_response(self, request, *args, **kwargs):
        response = super().finalize_response(request, *args, **kwargs)
        self._write_log(request, response)
        return response
