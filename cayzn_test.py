"""
    Coding test: Bookings report for a transportation operator

    Our revenue management solution CAYZN extracts from an inventory system the transport plan of an operator (trains,
    flights or buses with their itineraries, stops and timetable) and allows our users to analyze sales, forecast the
    demand and optimize their pricing.

    In this project you will manipulate related concepts to build a simple report. We will assess your ability to read
    existing code and to understand the data model in order to develop new features. Two items are essential: the final
    result, and the quality of your code.

    Questions and example data are at the bottom of the script. Do not hesitate to modify existing code if needed.

    Good luck!
"""

import datetime
from msilib.schema import tables
from typing import List


class Service:
    """A service is a facility transporting passengers between two or more stops at a specific departure date.

    A service is uniquely defined by its name and a departure date. It is composed of one or more legs (which
    represent its stops and its timetable), which lead to multiple Origin-Destination (OD) pairs, one for each possible
    trip that a passenger can buy.
    """

    def __init__(self, name: str, departure_date: datetime.date):
        self.name = name
        self.departure_date = departure_date
        self.legs: List[Leg] = []
        self.ods: List[OD] = []

    @property
    def day_x(self):
        """Number of days before departure.

        In revenue management systems, the day-x scale is often preferred because it is more convenient to manipulate
        compared to dates.
        """
        return (datetime.date.today() - self.departure_date).days

    @property
    def itinerary(self):
        """Returns ordered list of stations where the service stops.
        It is assumed that legs in a service are properly defined, without inconsistencies.
        """
        if len(self.legs) == 0:
            return []

        list_stops = []
        for leg in self.legs:
            list_stops.append(leg.origin)
        list_stops.append(self.legs[len(self.legs) - 1].destination)

        return list_stops

    def load_itinerary(self, itinerary: List["Station"]):
        """Creates legs and ODs associated to list of stations given."""

        self.legs = []
        self.ods = []
        if (len(itinerary) >= 2):
            # Legs
            for i in range(len(itinerary) - 1):
                self.legs.append(Leg(self, itinerary[i], itinerary[i + 1]))

            # ODs
            for i in range(len(itinerary)):
                for j in range(i + 1, len(itinerary)):
                    self.ods.append(OD(self, itinerary[i], itinerary[j]))

        return

    def load_passenger_manifest(self, passengers: List["Passenger"]):
        """Reads a passenger manifest (a list of all bookings made for this service).

        Allocates bookings across ODs. When called, it fills the `passengers` attribute of each OD instances
        belonging to the service.
        """

        for passenger in passengers:
            for od in self.ods:
                if (od.origin == passenger.origin and od.destination == passenger.destination):
                    od.passengers.append(passenger)
                    break

        return


class Station:
    """A station is where a service can stop to let passengers board or disembark."""

    def __init__(self, name: str, station_number: int):
        self.name = name
        self.station_number = station_number


class Leg:
    """A leg is a set of two consecutive stops.

    Example: a service whose itinerary is A-B-C-D has three legs: A-B, B-C and C-D.
    """

    def __init__(self, service: Service, origin: Station, destination: Station):
        self.service = service
        self.origin = origin
        self.destination = destination

    @property
    def passengers(self):
        """Returns passengers occupying a seat on this leg."""

        list_passengers = []
        for od in self.service.ods:
            if (od.origin.station_number <= self.origin.station_number):
                if (od.destination.station_number >= self.destination.station_number):
                    list_passengers += od.passengers

        return list_passengers


class OD:
    """An Origin-Destination (OD) represents the transportation facility between two stops, bought by a passenger.

    Example: a service whose itinerary is A-B-C-D has up to six ODs: A-B, A-C, A-D, B-C, B-D and C-D.
    """

    def __init__(self, service: Service, origin: Station, destination: Station):
        self.service = service
        self.origin = origin
        self.destination = destination
        self.passengers: List[Passenger] = []

    @ property
    def legs(self):
        """Legs that are crossed by this OD."""

        legs_crossed = []
        all_service_stops = self.service.itinerary
        try:
            first_stop = all_service_stops.index(self.origin)
            last_stop = all_service_stops.index(self.destination)
        except ValueError:
            return []

        for i in range(first_stop, last_stop):
            legs_crossed.append(self.service.legs[i])

        return legs_crossed

    def history(self):
        """Returns a list of data point, each data point is a three elements array:
        [day_x, cumulative number of bookings, cumulative revenue].

        """

        history = []
        for passenger in self.passengers:
            if not [passenger.sale_day_x, 0, 0] in history:
                history.append([passenger.sale_day_x, 0, 0])

        (cumulated_passengers, cumulated_price) = (0, 0)
        for day_x in history:
            for passenger in self.passengers:
                if (passenger.sale_day_x == day_x[0]):
                    day_x[1] += 1
                    day_x[2] += passenger.price

            day_x[1] += cumulated_passengers
            day_x[2] += cumulated_price
            (cumulated_passengers, cumulated_price) = (
                day_x[1], day_x[2])

        return history

    def see_availability(self, pricing, demand, forecast):
        """Books seats (or not) according to availabilities given in pricing."""

        counter = 0
        for price, request in demand:
            if (pricing[price] >= request):
                forecast[1] += request
                forecast[2] += request * price
                pricing[price] -= request
                break

            elif (pricing[price] < request):
                forecast[1] += pricing[price]
                forecast[2] += pricing[price] * price
                for i in range(counter, len(demand)):
                    demand[i][1] -= pricing[price]
                pricing[price] = 0

            counter += 1

        return (pricing, forecast)

    def forecast_initialization(self, history):
        """Initializes the list forecasts taking into account the history."""

        forecast_init = []
        (cumulated_passengers, cumulated_price) = (0, 0.0)
        for day_x in demand_matrix.keys():
            forecast_init.append(
                [day_x, cumulated_passengers, cumulated_price])

        forecast_init[0][1] = history[len(history) - 1][1]
        forecast_init[0][2] = float(history[len(history) - 1][2])
        return forecast_init

    def forecast(self, pricing, demand_matrix):
        """Forecasts accumulated sum of bookings and revenue per day-x up until D-0."""

        forecast_by_day = self.forecast_initialization(self.history())
        counter = 0
        for demand in demand_matrix.values():
            (pricing, forecast_by_day[counter]) = self.see_availability(
                pricing, list(map(list, demand.items())), forecast_by_day[counter])
            if (counter >= 1):
                forecast_by_day[counter][1] += forecast_by_day[counter - 1][1]
                forecast_by_day[counter][2] += forecast_by_day[counter - 1][2]
            counter += 1

        return forecast_by_day


class Passenger:
    """A passenger that has a booking on a seat for a particular origin-destination."""

    def __init__(self, origin: Station, destination: Station, sale_day_x: int, price: float):
        self.origin = origin
        self.destination = destination
        self.sale_day_x = sale_day_x
        self.price = price


# Let's create a service to represent a train going from Paris to Marseille with Lyon as intermediate stop. This service
# has two legs and sells three ODs.

ply = Station("ply", 1)  # Paris Gare de Lyon
lpd = Station("lpd", 2)  # Lyon Part-Dieu
msc = Station("msc", 3)  # Marseille Saint-Charles
service = Service("7601", datetime.date.today() + datetime.timedelta(days=7))
leg_ply_lpd = Leg(service, ply, lpd)
leg_lpd_msc = Leg(service, lpd, msc)
service.legs = [leg_ply_lpd, leg_lpd_msc]
od_ply_lpd = OD(service, ply, lpd)
od_ply_msc = OD(service, ply, msc)
od_lpd_msc = OD(service, lpd, msc)
service.ods = [od_ply_lpd, od_ply_msc, od_lpd_msc]

# 1. Add a property named `itinerary` in `Service` class, that returns the ordered list of stations where the service
# stops. Assume legs in a service are properly defined, without inconsistencies.

assert service.itinerary == [ply, lpd, msc]

# 2. Add a property named `legs` in `OD` class, that returns legs that are crossed by this OD. You can use the
# `itinerary` property to find the index of the matching legs.

assert od_ply_lpd.legs == [leg_ply_lpd]
assert od_ply_msc.legs == [leg_ply_lpd, leg_lpd_msc]
assert od_lpd_msc.legs == [leg_lpd_msc]

# 3. Creating every leg and OD for a service is not convenient, to simplify this step, add a method in `Service` class
# to create legs and ODs associated to list of stations. The signature of this method should be:
# load_itinerary(self, itinerary: List["Station"]) -> None:

itinerary = [ply, lpd, msc]
service = Service("7601", datetime.date.today() + datetime.timedelta(days=7))
service.load_itinerary(itinerary)
assert len(service.legs) == 2
assert service.legs[0].origin == ply
assert service.legs[0].destination == lpd
assert service.legs[1].origin == lpd
assert service.legs[1].destination == msc
assert len(service.ods) == 3
od_ply_lpd = next(od for od in service.ods if od.origin ==
                  ply and od.destination == lpd)
od_ply_msc = next(od for od in service.ods if od.origin ==
                  ply and od.destination == msc)
od_lpd_msc = next(od for od in service.ods if od.origin ==
                  lpd and od.destination == msc)

# 4. Create a method in `Service` class that reads a passenger manifest (a list of all bookings made for this service)
# and that allocates bookings across ODs. When called, it should fill the `passengers` attribute of each OD instances
# belonging to the service. The signature of this method should be:
# load_passenger_manifest(self, passengers: List["Passenger"]) -> None:

service.load_passenger_manifest(
    [
        Passenger(ply, lpd, -30, 20),
        Passenger(ply, lpd, -25, 30),
        Passenger(ply, lpd, -20, 40),
        Passenger(ply, lpd, -20, 40),
        Passenger(ply, msc, -10, 50),
    ]


)
od_ply_lpd, od_ply_msc, od_lpd_msc = service.ods
assert len(od_ply_lpd.passengers) == 4
assert len(od_ply_msc.passengers) == 1
assert len(od_lpd_msc.passengers) == 0

# 5. Write a property named `passengers` in `Leg` class that returns passengers occupying a seat on this leg.

assert len(service.legs[0].passengers) == 5
assert len(service.legs[1].passengers) == 1

# 6. We want to generate a report about sales made each day, write a `history()` method in `OD` class that returns a
# list of data point, each data point is a three elements array: [day_x, cumulative number of bookings, cumulative
# revenue].

history = od_ply_lpd.history()
assert len(history) == 3
assert history[0] == [-30, 1, 20]
assert history[1] == [-25, 2, 50]
assert history[2] == [-20, 4, 130]

# 7. We want to add to our previous report some forecasted data, meaning how many bookings and revenue are forecasted
# for next days. In revenue management, a number of seats is allocated for each price level. Let's say we only have 5
# price levels from 10€ to 50€. The following variable represents at a particular moment how many seats are available
# (values of the dictionary) at a given price (keys of the dictionary):

pricing = {10: 0, 20: 2, 30: 5, 40: 5, 50: 5}
# It means we have 2 seats at 20€, 5 at 30€ etc.

# To forecast our bookings, a machine learning algorithm has built the unconstrained demand matrix.
# For each day-x (number of days before departure) and each price level, this matrix gives the expected number of bookings:

demand_matrix = {
    -7: {10: 5, 20: 1, 30: 0, 40: 0, 50: 0},
    -6: {10: 5, 20: 2, 30: 1, 40: 1, 50: 1},
    -5: {10: 5, 20: 4, 30: 3, 40: 2, 50: 1},
    -4: {10: 5, 20: 5, 30: 4, 40: 3, 50: 1},
    -3: {10: 5, 20: 5, 30: 5, 40: 3, 50: 2},
    -2: {10: 5, 20: 5, 30: 5, 40: 4, 50: 3},
    -1: {10: 5, 20: 5, 30: 5, 40: 5, 50: 4},
    0: {10: 5, 20: 5, 30: 5, 40: 5, 50: 5}
}

# Thus, for instance, 5 days before departure (D-5) at price level 20€, the demand is 4
# If the demand cannot be fulfilled for a particular price because there are not enough seats remaining at this price level, all seats available at this price level
# are sold and the demand for upper price levels is reduced by this amount for the day.

# For every days before departure (day-x), we look at the lowest price level to know how much demand we have for this day-x.

# The forecasting algorithm, given the previously given `demand_matrix` and `pricing`, will give:
# ----------------------------------------------------------------------
# at D-7, 1 booking will be made at 20€
#   the new pricing is {10: 0, 20: *1*, 30: 5, 40: 5, 50: 5}
#   the new demand_matrix is
# demand_matrix = {
#     -7: {10: 5, 20: *0*, 30: 0, 40: 0, 50: 0},
#     -6: {10: 5, 20: 2, 30: 1, 40: 1, 50: 1},
#     .....
# }

# at D-6,
#   since the demand cannot be fullfiled (demand of 2 for 20€ but only one seat left at this price level), we will have
#      1 booking at 20€
#      the new pricing is {10: 0, 20: *0*, 30: 5, 40: 5, 50: 5}
#      the new demand_matrix is
#      demand_matrix = {
#         -7: {10: 5, 20: 0, 30: 0, 40: 0, 50: 0},
#         -6: {10: 5, 20: *1*, 30: *0*, 40: *0*, 50: *0*},
#         -5: {10: 5, 20: 4, 30: 3, 40: 2, 50: 1},
#         .....
#      }
#      since demand for price level 30€ is now 0, we stop there and there are no additional sales for this day-x.
#      (but if the original demand for D-6 and 30€ was 2, we would had have another sale at 30€)

# at D-5, 3 bookings are made at 30€
# and so on...

# Write a `forecast(pricing, demand_matrix)` method in `OD` class to forecast accumulated sum of bookings and
# revenue per day-x up until D-0, starting from the sales you add at end of question 6 (for instance, 4 sales on ply_lpd).

forecast = od_ply_lpd.forecast(pricing, demand_matrix)
assert len(forecast) == 8
assert forecast[0] == [-7, 5, 150.0]
assert forecast[1] == [-6, 6, 170.0]
assert forecast[2] == [-5, 9, 260.0]
assert forecast[3] == [-4, 12, 360.0]
assert forecast[4] == [-3, 15, 480.0]
assert forecast[5] == [-2, 18, 620.0]
assert forecast[6] == [-1, 21, 770.0]
assert forecast[7] == [0, 21, 770.0]
