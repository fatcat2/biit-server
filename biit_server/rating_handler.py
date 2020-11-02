from biit_server.meeting import Meeting
from biit_server.utils import send_discord_message
from biit_server.authentication import AuthenticatedType, authenticated
from .http_responses import http400, http500, jsonHttp200
from .query_helper import (
    ValidateType,
    validate_fields,
)
from .database import Database
from .rating import Rating, RatingAlreadySetException


@validate_fields(["meeting_id", "user", "rating", "token"], ValidateType.BODY)
@authenticated(AuthenticatedType.BODY)
def rating_post(request, auth):
    """Handles the rating POST endpoint
    Validates the keys in the request then calls the database to create a commmunity
    Args:
        request: A request object that contains a json object with keys: name, codeofconduct, Admins, Members, mpm, meettype, token

    Returns:
        (json): Http 200 string response containing the  refresh token and new token

    Raises:
        Http 400 when the json is missing a key
    """
    body = request.get_json()

    rating_db = Database("ratings")

    rating_snapshot = rating_db.get(body["meeting_id"])

    if rating_snapshot == False:
        rating = Rating(
            meeting_id=body["meeting_id"], rating_dict={body["user"]: body["rating"]}
        )

        success = rating_db.add(rating.to_dict(), id=body["meeting_id"])

    else:
        rating = Rating(document_snapshot=rating_snapshot)
        try:
            rating.set_rating(body["user"], body["rating"])
        except RatingAlreadySetException:
            return http400(f"Rating for user {body['user']} has already been set")

        success = rating_db.update(
            body["meeting_id"], {"rating_dict": rating.get_ratings()}
        )

    if not success:
        return http400(
            f"Error in updating meeting id {body['meeting_id']} in Firestore database."
        )

    response = {
        "access_token": auth[0],
        "refresh_token": auth[1],
        "data": rating.to_dict(),
    }

    return jsonHttp200("Rating created", response)

@validate_fields(["user", "token"], ValidateType.BODY)
@authenticated(AuthenticatedType.BODY)
def rating_post(request, auth):
    """Handles the rating POST endpoint
    Validates the keys in the request then calls the database to get all unrated meetups
    Args:
        request: A request object that contains a json object with keys: user, token

    Returns:
        (json): Http 200 string response containing the  refresh token and new token

    Raises:
        Http 400 when the json is missing a key
    """
    body = request.get_json()

    rating_db = Database("ratings")

    rating_snapshot = rating_db.get(body["meeting_id"])

    if rating_snapshot == False:
        rating = Rating(
            meeting_id=body["meeting_id"], rating_dict={body["user"]: body["rating"]}
        )

        success = rating_db.add(rating.to_dict(), id=body["meeting_id"])

    else:
        rating = Rating(document_snapshot=rating_snapshot)
        try:
            rating.set_rating(body["user"], body["rating"])
        except RatingAlreadySetException:
            return http400(f"Rating for user {body['user']} has already been set")

        success = rating_db.update(
            body["meeting_id"], {"rating_dict": rating.get_ratings()}
        )

    if not success:
        return http400(
            f"Error in updating meeting id {body['meeting_id']} in Firestore database."
        )

    response = {
        "access_token": auth[0],
        "refresh_token": auth[1],
        "data": rating.to_dict(),
    }

    return jsonHttp200("Rating created", response)


@validate_fields(["meeting_id", "token"], ValidateType.QUERY)
@authenticated(AuthenticatedType.QUERY)
def rating_get(request, auth):
    """Handles the rating GET endpoint
        Validates the keys in the request then calls the database to get information about a commmunity
    Args:
        request: A request object that contains a json object with keys: name

    Returns:
        (str): Http 200 string response containing information about the searched community

    Raises:
        Http 400 when the json is missing a key
    """
    args = request.args

    rating_db = Database("ratings")

    rating_db_response = rating_db.get(args["meeting_id"])

    if not rating_db_response:
        return http500(f"Error in retrieving rating from Firestore database.", "Lucas")

    rating = Rating(document_snapshot=rating_db_response)

    try:
        response = {
            "access_token": auth[0],
            "refresh_token": auth[1],
            "data": rating.to_dict(),
        }
        return jsonHttp200("Rating Received", response)
    except:
        send_discord_message(f'Rating with id [{args["meeting_id"]}] does not exist')
        return http500("Rating not found")

@validate_fields(["email", "token"], ValidateType.QUERY)
@authenticated(AuthenticatedType.QUERY)
def rating_get_pending(request, auth):
    """Handles the rating GET endpoint
        Validates the keys in the request then calls the database to get information about a commmunity
    Args:
        request: A request object that contains a json object with keys: name

    Returns:
        (str): Http 200 string response containing information about the searched community

    Raises:
        Http 400 when the json is missing a key
    """
    args = request.args

    rating_db = Database("ratings")

    rating_db_response = rating_db.collection_ref.get()

    print(rating_db_response)

    ratings = [
        Rating(document_snapshot=rating_snapshot)
        for rating_snapshot in rating_db_response
    ]
    
    # Finds the ratings the user is a part of and
    # and has not yet rated.
    ratings  = [
        rating.to_dict() for rating in ratings
        if args["email"] in rating.rating_dict and
        rating.rating_dict[args["email"]] == -1
    ]

    if not rating_db_response:
        return http500(f"Error in retrieving rating from Firestore database.", "Lucas")

    try:
        response = {
            "access_token": auth[0],
            "refresh_token": auth[1],
            "data": ratings,
        }
        return jsonHttp200("Rating Received", response)
    except:
        send_discord_message(f'Rating with id [{args["meeting_id"]}] does not exist')
        return http500("Rating not found")