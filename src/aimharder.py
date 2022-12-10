import os
import logging
from dotenv import load_dotenv
from .aimharder_client import AimharderClient
from .error import AimharderResponseError
from .training import Training
from .utils import read_file, write_file, empty_file

load_dotenv()
logger = logging.getLogger(__name__)
BOOKING_FILENAME = 'aimharder_booking.pickle'

class Aimharder:

    def __init__(self):
        self.aimharder_client = AimharderClient(os.getenv('USERNAME'), os.getenv('PASSWORD'))
        self.trainings = []
        self.booked_training = read_file(BOOKING_FILENAME)
        if self.booked_training is not None:
            logger.info('Recovered training(%s) booked for %s of the date %s with booking_id %s', self.booked_training.id, self.booked_training.class_name, self.booked_training.date, self.booked_training.booking_id)

    def list_trainings_by_date(self, date) -> [Training]:
        bookings = self.aimharder_client.get_bookings(date)
        logger.info('Obtained a list of %s trainings by day %s', len(bookings), date)
        self.trainings = list(map(lambda booking: Training(booking, date), bookings))
        return self.trainings

    def book_training(self, training_id) -> bool:
        try:
            [selected_training] = list(filter(lambda training: training.id == training_id, self.trainings))
            response_booking = self.aimharder_client.book(selected_training.id, selected_training.date)
            selected_training.booking_id = response_booking['booking_id']
            self.booked_training = selected_training
            logger.info('Training(%s) %s booked for the date %s by booking_id %s', training_id, self.booked_training.class_name, self.booked_training.date, self.booked_training.booking_id)
            write_file(BOOKING_FILENAME, self.booked_training)
            logger.info('Saved training %s by booking_id %s', training_id, self.booked_training.booking_id)
            return True
        except AimharderResponseError as error:
            logger.error('Couldn\'t book training by training_id %s: %s', training_id, error)
            return False

    def cancel_training(self) -> bool:
        try:
            response_booking = self.aimharder_client.cancel_booking(self.booked_training.booking_id)
            is_cancelled = response_booking['cancel']
            if is_cancelled:
                logger.info('Cancelled training %s by booking_id %s', self.booked_training.id, self.booked_training.booking_id)
                self.booked_training = None
                empty_file(BOOKING_FILENAME)
                logger.info('Deleted training %s by booking_id %s', self.booked_training.id, self.booked_training.booking_id)
            return is_cancelled
        except AimharderResponseError as error:
            logger.error('Couldn\'t cancel the training by training_id %s: %s', self.booked_training.booking_id, error)
            return False
