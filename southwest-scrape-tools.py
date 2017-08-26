#!/usr/bin/env python
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
#
#       tools for scarping current southwest
#       airlines flight data
#
#~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from pyvirtualdisplay import Display
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from bs4 import BeautifulSoup
import time

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
def fetch_flight_data(webdriver):
    
    table_elem  = webdriver.find_element(By.ID, 'faresOutbound')
    soup = BeautifulSoup(table_elem.get_attribute('innerHTML'))
    result_rows = soup.findAll('tr', id=lambda x: x and 'outbound_flightRow' in x)

    for elem in result_rows:

        # get departure time
        depart_time = elem.find('td', {'class':'depart_column'}).find('span', {'class','bugText'}).get_text()

        print 'departure time: ' + depart_time

        # get arrival time
        arrive_time = soup.find('td', {'class':'arrive_column'}).find('span', {'class','bugText'}).get_text()
        arrive_time = arrive_time.replace('\n', ' ').strip() # clean up

        print 'arrival time: ' + arrive_time

        # get flight number(s)
        flight_info = soup.find('td', {'class':'flight_column'})

        # get all flights (connecting/final)
        flights = flight_info.find_all('div', class_=lambda x: x and 'aircraft_information' and 'right' in x)
    
        flight_info_dict = {}
        index = 0
        for flight_info in flights:
            
            flight_num, plane_type, seat_num = parse_flight_info(flight_info.text)
            flight_info_dict[index] = [flight_num, plane_type, seat_num]

        for key in flight_info_dict.keys():
            print 'flight number: ' + flight_info_dict[key][0]
            print 'plane type: ' + flight_info_dict[key][1]
            print 'number seats: ' + flight_info_dict[key][2]

        # get number of  connecting stops
        connect_num = soup.find('div', {'class':'flightDetailsContainer'}).find('span', {'class':'headerText'})
        connect_num = connect_num.text.strip('(').split()[0]
        
        # get connecting stops
        connecting_stops = parse_routing_info(soup.find('table', {'class':'routingDetailsContainer'}), int(connect_num))






# helper function to get flight #, aircraft type, # seats from flight info
def parse_flight_info(flight_info_text):

    # split into list
    flight_info_list = flight_info_text.split()
    
    # get flight number
    flight_num = flight_info_list[flight_info_list.index('#')+1]

    # get aircraft type
    plane_type = flight_info_list[flight_info_list.index('Type:')+1] + ' ' + flight_info_list[flight_info_list.index('Type:')+2]

    # get number of seats
    seat_num = flight_info_list[flight_info_list.index('Seats:')+1]

    return flight_num, plane_type, seat_num

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
    




'''
def 

# this gets us all rows of flight data
driver.find_elements_by_css_selector("tr[id^=outbound_flightRow]")

# make into BS
soup = BeautifulSoup(elem[0].get_attribute('innerHTML'))

# get depart time
soup.find_all("td", {"class":"depart_column"})[0].select('.bugText').get_text()
'''    
