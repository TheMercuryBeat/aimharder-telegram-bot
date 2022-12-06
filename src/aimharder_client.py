import os
import logging
from typing import Any
from requests import Session, Response, HTTPError
from bs4 import BeautifulSoup
from http import HTTPStatus
from dotenv import load_dotenv
from .error import TooManyAttemptsError, UnknownError, AimharderError, AimharderResponseError
from .utils import read_file, write_file

load_dotenv()
logger = logging.getLogger(__name__)

MESSAGE_LOGIN_ERRORS = 'loginErrors'
MESSAGE_UNKNOWN = "Unknown error"
MESSAGE_TOO_MANY_ATTEMPTS = "Unknown error"

LOGIN_URL = f'https://aimharder.com/login'
API_DOMAIN = f'https://{os.getenv("BOX_NAME")}.aimharder.com'
GET_BOOKINGS_URL = f'{API_DOMAIN}/api/bookings'
BOOK_URL = f'{API_DOMAIN}/api/book'
CANCEL_BOOK_URL = f'{API_DOMAIN}/api/cancelBook'
SESSION_FILEPATH = f'{os.getenv("PICKLE_FILEPATH")}/aimharder_session.pickle'


def handler_response(response, action) -> dict[str, Any]:
    try:
        response.raise_for_status()
        response = response.json()
        logger.debug('Received response %s', response)
        if 'bookState' in response and response['bookState'] == 1:
            if 'id' in response:
                return {'booking_id': response['id']}
            else:
                return {'cancel': True}
        elif 'bookState' in response and 'errorMssg' in response:
            raise AimharderResponseError(action, response['bookState'], response['errorMssg'], response)
        else:
            raise AimharderResponseError(action, response['bookState'], 'unknown', response)
    except HTTPError as error:
        logger.error('An error occurred: %s', error)
        raise AimharderError(str(error))


class AimharderClient:

    def __init__(self, email: str, password: str):
        self.box_id = os.getenv('BOX_ID')
        self.session = read_file(SESSION_FILEPATH, email)

        if self.session is None:
            logger.info('No found session by %s user', email)
            self.session = self.__login(email, password)
            write_file(SESSION_FILEPATH, {email: self.session})
            logger.info('Saved session by %s user', email)
        else:
            logger.info('Found session by %s user', email)

    @staticmethod
    def __validate_login(response: Response) -> None:
        soup = BeautifulSoup(response.content, "html.parser").find(id=MESSAGE_LOGIN_ERRORS)
        if soup is not None:
            logger.warning('No valid login!')
            if MESSAGE_TOO_MANY_ATTEMPTS in soup.text:
                raise TooManyAttemptsError()
            elif MESSAGE_UNKNOWN in soup.text:
                raise UnknownError()

    @staticmethod
    def __login(email: str, password: str) -> Session:
        session = Session()
        payload = {'login': 'Iniciar sesión', 'loginiframe': 0, "mail": email, "pw": password}
        logger.debug('Logging user %s...', email)
        response = session.post(LOGIN_URL, data=payload)
        AimharderClient.__validate_login(response)
        logger.info('Logged user %s', email)
        return session

    def get_bookings(self, date: str) -> [dict]:
        params = {"box": self.box_id, "day": date, "familyId": ""}
        response = self.session.get(GET_BOOKINGS_URL, params=params)
        bookings = response.json()['bookings'] if response.status_code == HTTPStatus.OK else []
        return bookings

    def book(self, booking_id: int, booking_date: str) -> dict[str, Any]:
        payload = {"id": booking_id, "day": booking_date, "insist": 0, "familyId": ''}
        response = self.session.post(BOOK_URL, data=payload)
        return handler_response(response, 'book')

    def cancel_booking(self, booking_id: int) -> dict[str, Any]:
        payload = {'id': booking_id, 'late': 0, 'familyId': ''}
        response = self.session.post(CANCEL_BOOK_URL, data=payload)
        return handler_response(response, 'cancel_booking')
