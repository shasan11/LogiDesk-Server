from rest_framework import serializers
from djoser.serializers import (
    UserCreateSerializer as BaseUserCreateSerializer,
    UserSerializer as BaseUserSerializer,
)
from django.contrib.auth.models import Group
from master.models import Branch
from .models import CustomUser


class BranchCoreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = "__all__"


class CustomUserCreateSerializer(BaseUserCreateSerializer):
    # matches your model
    branch = serializers.PrimaryKeyRelatedField(
        queryset=Branch.objects.all(),
        required=False,
        allow_null=True,
    )
    profile = serializers.ImageField(required=False, allow_null=True)

    # allow setting groups during signup (optional)
    groups = serializers.PrimaryKeyRelatedField(
        queryset=Group.objects.all(),
        many=True,
        required=False,
        write_only=True,
    )

    user_type = serializers.ChoiceField(
        choices=CustomUser.UserType.choices,
        required=False,
        allow_null=True,
    )

    class Meta(BaseUserCreateSerializer.Meta):
        model = CustomUser
        fields = (
            "id",
            "email",
            "username",
            "password",
            "first_name",
            "last_name",
            "branch",
            "profile",
            "user_type",
            "groups",
        )
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, attrs):
        attrs = super().validate(attrs)

        # Optional: basic sanity check
        # (Your model allows user_type null/blank, so don't force it.)
        user_type = attrs.get("user_type", None)
        if user_type is not None and user_type not in dict(CustomUser.UserType.choices):
            raise serializers.ValidationError({"user_type": "Invalid user type."})

        return attrs

    def create(self, validated_data):
        groups = validated_data.pop("groups", [])
        user = super().create(validated_data)

        if groups:
            user.groups.set(groups)

        return user


class CustomUserSerializer(BaseUserSerializer):
    profile_url = serializers.SerializerMethodField()
    groups = serializers.SerializerMethodField()
    branch = serializers.SerializerMethodField()

    class Meta(BaseUserSerializer.Meta):
        model = CustomUser
        fields = (
            "id",
            "email",
            "username",
            "first_name",
            "last_name",
            "user_type",
            "branch",
            "profile",
            "profile_url",
            "groups",
            "is_active",
            "is_superuser",
        )

    def get_profile_url(self, obj):
        if obj.profile and hasattr(obj.profile, "url"):
            return obj.profile.url
        return None

    def get_groups(self, obj):
        # return ids; change to names if you prefer
        return list(obj.groups.values_list("id", flat=True))

    def get_branch(self, obj):
        # return a clean object or null (better than raw id for frontend)
        if not obj.branch:
            return None
        return {"id": obj.branch_id, "name": getattr(obj.branch, "name", str(obj.branch))}