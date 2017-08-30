#!/usr/bin/env python
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#       tools for scrping current southwest
#       airlines flight data 
#   
#       EXCLUSIVELY FOR RESEARCH PURPOSES
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import datetime
import re

# must be on southwest.com homepage
def southwest_search(webdriver, one_way, origin, destination, departure_date, return_date):
    
    # first have to make sure we can send keys to boxes
    WebDriverWait(webdriver, 10).until(
        EC.element_to_be_clickable((By.NAME, 'originAirport'))
    )

    # specify if looking for 1 way or round trip    
    if one_way:
        webdriver.find_element(By.ID, "trip-type-one-way").click()

    else:
        webdriver.find_element(By.ID, "trip-type-round-trip").click()

    # make sure we've deleted all pre-inputted input
    N = 9
    webdriver.find_element(By.NAME, 'originAirport').send_keys(Keys.BACKSPACE * N)
    webdriver.find_element(By.NAME, 'destinationAirport').send_keys(Keys.BACKSPACE * N)
    webdriver.find_element(By.ID, 'air-date-departure').send_keys(Keys.BACKSPACE * N)
    
    if not one_way:
        webdriver.find_element(By.ID, 'air-date-return').send_keys(Keys.BACKSPACE * N)

    # input specified parameters
    webdriver.find_element(By.NAME, 'originAirport').send_keys(origin)

    webdriver.find_element(By.NAME, 'destinationAirport').send_keys(destination)

    webdriver.find_element(By.ID, 'air-date-departure').send_keys(departure_date) #has to be MM/DD format!

    if not one_way:
        webdriver.find_element(By.ID, 'air-date-return').send_keys(return_date)

    webdriver.find_element(By.ID, 'jb-booking-form-submit-button').send_keys(Keys.ENTER)


# once we have our search results, put all results into array of arrays
def fetch_flight_data(webdriver, search_date): # search_date must be in dd/mm/yy format
    
    table_elem  = webdriver.find_element(By.ID, 'faresOutbound')
    soup = BeautifulSoup(table_elem.get_attribute('innerHTML'))
    result_rows = soup.findAll('tr', id=lambda x: x and 'outbound_flightRow' in x)
    index = -1
    for elem in result_rows:

        depart_time, arrive_time = get_arrival_departure_time(elem, search_date)

        # get list flight leg info
        flight_leg_info = parse_leg_info(elem)

        # get number of  connecting stops
        connect_num = elem.find('div', {'class':'flightDetailsContainer'}).find('span', {'class':'headerText'})
        connect_num = connect_num.text.strip('(').split()[0]
        
        # get connecting stops
        if 'Nonstop' in connect_num:
            connect_num = 'Nonstop'
            connecting_stops = []
        else:
            connecting_stops = parse_routing_info(elem.find('table', {'class':'routingDetailsContainer'}), int(connect_num))

        index += 1

        # get flight duration
        flight_duration = parse_flight_duration(elem)

        # get prices
        prices = parse_prices(elem)

        # TESTING PRINTS
        print "result %d" %index
        print "departure time: " + str(depart_time) + ", arrival time: " + str(arrive_time)
        print "flight duration: {}".format(flight_duration)
        print "first leg info : {}".format(flight_leg_info[0])
        print "second leg info : {}".format(flight_leg_info[1])
        print "third leg info : {}".format(flight_leg_info[2])
        print "fourth leg info : {}".format(flight_leg_info[3])
        print "there are {} connecting stops : {}".format(connect_num, connecting_stops)
        print "PRICES: {}".format(prices)
        print '\n\n\n'

# get arrival/departure times for a particular results row
def get_arrival_departure_time(row_soup, search_date): # search_date must be string

        # get departure time
        depart_time = row_soup.find('td', {'class':'depart_column'}).find('span', {'class','bugText'}).get_text()
        depart_datetime = datetime.datetime.strptime(search_date + ' ' + depart_time, '%m/%d/%y %I:%M %p')
        
        # get arrival time
        arrive_time = row_soup.find('td', {'class':'arrive_column'}).find('span', {'class','bugText'}).get_text()
        arrive_time = arrive_time.replace('\n', ' ').strip() # clean up

        if 'Next Day' in arrive_time:
            add_day = datetime.timedelta(days=1)
            arrive_time = arrive_time.strip('Next Day')
        else:
            add_day = datetime.timedelta(days=0)

        arrive_datetime = datetime.datetime.strptime(search_date + ' ' + arrive_time, '%m/%d/%y %I:%M %p') + add_day

        return depart_datetime, arrive_datetime




# helper function to get flight #, aircraft type, # seats for each flight leg
def parse_leg_info(soup):

    # initial parsing
    flight_info = soup.find('td', {'class':'flight_column'})

    # get block of flight leg (connecting/final) info
    leg_info= [x for x in flight_info.select('.flightInformation') if 'Aircraft Information' in x.find('h6').text][0]
    flight_legs = leg_info.select('.aircraft_information')

    assert(len(flight_legs) < 5)

    # initiate flight list with all blanks (assume maximum of 4 flight legs for 1 purchases flight)
    leg_list = [['', '', '']] * 4

    index = 0
    for info in flight_legs:
        
         # split into list
        flight_info_list = info.text.split()
        
        # get flight number
        flight_num = flight_info_list[flight_info_list.index('#')+1]

        # get aircraft type
        plane_type = flight_info_list[flight_info_list.index('Type:')+1] + ' ' + flight_info_list[flight_info_list.index('Type:')+2]
        # no separation between "Boeing 747" and "No." for # of seats
        plane_type = plane_type.replace('No.', '')

        # get number of seats
        seat_num = flight_info_list[flight_info_list.index('Seats:')+1]

        leg_list[index] = [flight_num, plane_type, seat_num]    
    
        index += 1

    return leg_list


# parse routing info, have to input routing info table
def parse_routing_info(routing_table, num_stops):
    
    stop_list = []
    
    try:
        plane_change = routing_table.find_all('span', {'class':'routingDetailsChangePlanesText'})
        plane_change = [z.text for z in plane_change if ',' in z.text][0].strip()
        stop_list.append(plane_change)

    except IndexError:
        pass

    # if we didn't get a stop with plane change info or are looking at a 2 stop flight
    if len(stop_list) < num_stops:
        stop_list.append(routing_table.find('div', {'class':'additionalStopList'}).text.strip())

    return stop_list
    

# entire flight length (assumes duration expressed only in hours, minutes)
def parse_flight_duration(soup):

    # simple regex
    hour, minute = re.findall(r'\d+', soup.select('.bugText.duration')[0].text)

    # return zero-padded hr:zero-padded minute
    return hour.zfill(2) + ':' + minute.zfill(2) 


# get 3 different prices
def parse_prices(soup):

    price_html_blocks = soup.select('.price_column')

    price_list = []

    for price_html in price_html_blocks:
    
        price = price_html.find('label', {'class':'product_price'}).text.strip()
        price_list.append(price)

    return price_list


