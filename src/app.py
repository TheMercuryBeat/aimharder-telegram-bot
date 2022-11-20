import os
from dotenv import load_dotenv
from .aimharder import Aimharder
from .error import AimharderResponseError
from .training import Training
from .utils import read_file, write_file, empty_file

BOOKING_FILEPATH = f'{os.getenv("PICKLE_FILEPATH")}/aimharder_booking.pickle'


class App:

    def __init__(self):
        load_dotenv()
        self.aimharder = Aimharder(os.getenv('USERNAME'), os.getenv('PASSWORD'))
        self.trainings = []
        self.booked_training = read_file(BOOKING_FILEPATH)

    def list_trainings_by_date(self, date) -> [Training]:
        bookings = self.aimharder.get_bookings(date)
        self.trainings = list(map(lambda booking: Training(booking, date), bookings))
        return self.trainings

    def book_training(self, training_id) -> bool:
        try:
            [selected_training] = list(filter(lambda training: training.id == training_id, self.trainings))
            response_booking = self.aimharder.book(selected_training.id, selected_training.date)
            selected_training.booking_id = response_booking['booking_id']
            self.booked_training = selected_training
            write_file(BOOKING_FILEPATH, self.booked_training)
            return True
        except AimharderResponseError as error:
            return False

    def get_book_training(self, date) -> Training:
        bookings = self.aimharder.get_bookings(date)
        trainings = list(map(lambda booking: Training(booking, date), bookings))
        [selected_training] = list(filter(lambda training: training.book_state == '1', trainings))
        return selected_training

    def cancel_training(self) -> bool:
        try:
            response_booking = self.aimharder.cancel_booking(self.booked_training.booking_id)
            is_cancelled = response_booking['cancel']
            if is_cancelled:
                self.booked_training = None
                empty_file(BOOKING_FILEPATH)
            return is_cancelled
        except AimharderResponseError as error:
            return False
