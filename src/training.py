class Training:

    def __init__(self, booking, date):
        self.id = booking['id']
        self.time = booking['time']
        self.time_id = booking['timeid']
        self.class_id = booking['classId']
        self.class_name = booking['className']
        self.coach_name = booking['coachName']
        self.ocupation = booking['ocupation']
        self.limit = booking['limit']
        self.booking_id = booking['idres']
        self.book_state = booking['bookState']
        self.date = date

    def __str__(self):
        return f'{self.time} -> {self.class_name} ({"{:02}".format(int(self.ocupation))}/{self.limit}), ' \
               f'Monitor {self.coach_name}'
