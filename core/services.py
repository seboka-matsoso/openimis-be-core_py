from django.apps import apps
from core.models import User, InteractiveUser, Officer, UserRole

import logging

logger = logging.getLogger(__file__)


def create_or_update_interactive_user(user_id, data, audit_user_id, connected):
    i_fields = {
        "username": "login_name",
        "other_names": "other_names",
        "last_name": "last_name",
        "phone_number": "phone",
        "email": "email",
        "language": "language_id",
        "health_facility_id": "health_facility_id",
    }
    data_subset = {v: data.get(k) for k, v in i_fields.items()}
    data_subset["audit_user_id"] = audit_user_id
    data_subset["role_id"] = data["roles"][0]  # The actual roles are stored in their own table
    data_subset["is_associated"] = connected
    if user_id:
        # TODO we might want to update a user that has been deleted. Use Legacy ID ?
        i_user = InteractiveUser.objects.filter(validity_to__isnull=True, user__id=user_id).first()
    else:
        i_user = None
    if i_user:
        i_user.save_history()
        [setattr(i_user, k, v) for k, v in data_subset.items()]
        if "password" in data:
            i_user.set_password(data["password"])
        created = False
    else:
        # verify whether the username is already taken, as we will update it regardless
        already_exists = InteractiveUser.objects.filter(
            login_name=data_subset["login_name"],
            validity_to__isnull=True
        ).exists()
        if already_exists:
            raise Exception("username already exists")  # TODO improve Exception
        i_user = InteractiveUser(**data_subset)
        if "password" in data:
            i_user.set_password(data["password"])
        else:
            # No password provided for creation, will have to be set later.
            i_user.stored_password = "locked"
        created = True

    # TODO update regions (doesn't seem to do anything on the server and there is no table to store the data)
    i_user.save()
    create_or_update_user_roles(i_user, data["roles"])
    return i_user, created


def create_or_update_user_roles(i_user, role_ids):
    from core import datetime
    now = datetime.datetime.now()
    UserRole.objects.filter(user=i_user, validity_to__isnull=True).update(validity_to=now)
    for role_id in role_ids:
        UserRole.objects.update_or_create(user=i_user, role_id=role_id, defaults={"validity_to": None})


# TODO move to location module ?
def create_or_update_user_districts(i_user, district_ids):
    # To avoid a static dependency from Core to Location, we'll dynamically load this class
    user_district_class = apps.get_model("location", "UserDistrict")
    from core import datetime
    now = datetime.datetime.now()
    user_district_class.objects.filter(user=i_user, validity_to__isnull=True).update(validity_to=now)
    for district_id in district_ids:
        user_district_class.objects.update_or_create(
            user=i_user, district_id=district_id, defaults={"validity_to": None})


def create_or_update_officer_villages(officer, village_ids):
    # To avoid a static dependency from Core to Location, we'll dynamically load this class
    officer_village_class = apps.get_model("location", "OfficerVillage")
    from core import datetime
    now = datetime.datetime.now()
    officer_village_class.objects\
        .filter(officer=officer, validity_to__isnull=True)\
        .update(validity_to=now)
    for village_id in village_ids:
        officer_village_class.objects.update_or_create(
            officer=officer, location_id=village_id, defaults={"validity_to": None})


def create_or_update_officer(user_id, data, audit_user_id, connected):
    officer_fields = {
        "username": "code",
        "other_names": "other_names",
        "last_name": "last_name",
        "phone_number": "phone",
        "email": "email",
        "birth_date": "dob",
        "address": "address",
        "works_to": "works_to",
        "health_facility_id": "location",
        # TODO veo_code, last_name, other_names, dob, phone
        "substitution_officer_id": "substitution_officer_id",
    }
    data_subset = {v: data.get(k) for k, v in officer_fields.items()}
    data_subset["audit_user_id"] = audit_user_id
    data_subset["has_login"] = connected
    if user_id:
        # TODO we might want to update a user that has been deleted. Use Legacy ID ?
        officer = Officer.objects.filter(validity_to__isnull=True, user__id=user_id).first()
    else:
        officer = None
    if officer:
        officer.save_history()
        [setattr(officer, k, v) for k, v in data_subset.items()]
        created = False
    else:
        # verify whether the username is already taken, as we will update it regardless
        already_exists = Officer.objects.filter(
            code=data_subset["code"],
            validity_to__isnull=True
        ).exists()
        if already_exists:
            raise Exception("username/code already exists")  # TODO improve Exception
        officer = Officer(**data_subset)
        created = True

    officer.save()
    if data["village_ids"]:
        create_or_update_officer_villages(officer, data["village_ids"])
    return officer, created


def create_or_update_claim_admin(user_id, data, audit_user_id, connected):
    ca_fields = {
        "username": "code",
        "other_names": "other_names",
        "last_name": "last_name",
        "phone_number": "phone",
        "email": "email_id",
        "birth_date": "dob",
        "health_facility_id": "health_facility_id",
    }
    data_subset = {v: data.get(k) for k, v in ca_fields.items()}
    data_subset["audit_user_id"] = audit_user_id
    data_subset["has_login"] = connected
    # Since ClaimAdmin is not in the core module, we have to dynamically load it.
    # If the Claim module is not loaded and someone requests a ClaimAdmin, this will raise an Exception
    claim_admin_class = apps.get_model("claim", "ClaimAdmin")
    if user_id:
        # TODO we might want to update a user that has been deleted. Use Legacy ID ?
        claim_admin = claim_admin_class.objects.filter(validity_to__isnull=True, user__id=user_id).first()
    else:
        claim_admin = None
    if claim_admin:
        claim_admin.save_history()
        [setattr(claim_admin, k, v) for k, v in data_subset.items()]
        created = False
    else:
        # verify whether the username is already taken, as we will update it regardless
        already_exists = claim_admin_class.objects.filter(
            code=data_subset["code"],
            validity_to__isnull=True
        ).exists()
        if already_exists:
            raise Exception("username/code already exists")  # TODO improve Exception
        claim_admin = claim_admin_class(**data_subset)
        created = True

    # TODO update municipalities, regions
    claim_admin.save()
    return claim_admin, created


def create_or_update_core_user(user_uuid, username, i_user=None, t_user=None, officer=None, claim_admin=None):
    if user_uuid:
        # This intentionally fails if the provided uuid doesn't exist as we don't want clients to set it
        user = User.objects.get(id=user_uuid)
        # There is no history to save for User
        if user.username != username:
            logger.warning("Ignored attempt to change the username of %s from %s to %s. This is not supported",
                           user_uuid, user.username, username)
        created = False
    else:
        user = User(username=username)
        created = True

    if i_user:
        user.i_user = i_user
    if t_user:
        user.t_user = t_user
    if officer:
        user.officer = officer
    if claim_admin:
        user.claim_admin = claim_admin
    user.save()
    return user, created
