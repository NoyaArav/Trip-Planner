import requests
import datetime
from serpapi import GoogleSearch


# Set up OpenAI API credentials
openai_api_key = "sk-proj-wQ4taTDDFhbuDrmkqIlOT3BlbkFJlJVo8Zlx0wucOcJ2atou"
openai_api_model = "gpt-3.5-turbo"

# Set up SerpAPI API credentials
serpapi_api_key = "e0bdc813b6c92ed8d4b6521577f17ab892d5a09e397d74b1fb405bfb838cbcef"

def get_user_input():
    start_date_str = input("Enter the start date of your trip (YYYY-MM-DD): ")
    end_date_str = input("Enter the end date of your trip (YYYY-MM-DD): ")
    budget = float(input("Enter your total budget in USD for the trip: "))
    trip_type = input("Enter the type of trip (ski/beach/city): ")
    
    return start_date_str, end_date_str, budget, trip_type

def parse_dates(start_date_str, end_date_str):
    try:
        start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d')
        num_days = (end_date - start_date).days
    except ValueError:
        print(f"Invalid date format. Please enter dates in the format: (YYYY-MM-DD)")
        exit()
        
    return start_date, end_date, num_days

def validate_dates(start_date, end_date):
    if start_date > end_date:
        raise ValueError("Start date must be before end date.")
    if start_date < datetime.datetime.now():
        raise ValueError("Start date must be in the future.")
    

def get_destination_suggestions(start_date, trip_type):
    trip_month = start_date.strftime('%B')
    prompt = f"Suggest 5 best places to visit in the month of {trip_month} for a {trip_type} trip. Start each location with the arrival airport code in uppercase, followed by a colon and the destination name."
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {openai_api_key}"
            },
            json={
                "messages": [
                    {"role": "system", "content": "Start"},
                    {"role": "user", "content": prompt}
                ],
                "model": openai_api_model
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            # Extract messages where role is 'assistant'
            suggestion_text = data["choices"][0]["message"]["content"].strip()
            suggestions = suggestion_text.split("\n")
            return suggestions
        elif response.status_code == 401:
            raise Exception("Looks like your OpenAI API key is incorrect. Please check your API key and try again.")
        else:
            raise Exception(f"Failed to fetch from OpenAI API. Status code: {response.status_code}, Response: {response.text}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        return []
    
    
def get_flight_price_insights(departure_id, arrival_id, departure_date, return_date):

    try:
        params = {
            "engine": "google_flights",
            "departure_id": departure_id,
            "arrival_id": arrival_id,
            "outbound_date": departure_date.strftime("%Y-%m-%d"),
            "return_date": return_date.strftime("%Y-%m-%d"),
            "currency": "USD",
            "hl": "en",
            "api_key": serpapi_api_key
        }
        
        response = requests.get("https://serpapi.com/search", params=params)
        
        if response.status_code == 200:
            data = response.json()
            price_insights = data.get("price_insights", {})
            if price_insights:
                lowest_price = price_insights.get("lowest_price", 0)
                return lowest_price
            else:
                return None
        else:
            raise Exception(f"Failed to fetch from SerpAPI. Status code: {response.status_code}, Response: {response.text}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None
    
    
    
def get_most_expensive_hotel(destination, check_in_date, check_out_date, max_price, num_days):
    max_price_per_night = max_price / num_days
    min_price_per_night = int(max_price_per_night * 0.65)  # Set minimum price to 75% of the max price per night to avoid unnecessary serpapi searches

    params = {
        "engine": "google_hotels",
        "q": destination,
        "check_in_date": check_in_date.strftime("%Y-%m-%d"),
        "check_out_date": check_out_date.strftime("%Y-%m-%d"),
        "adults": "1",
        "currency": "USD",
        "hl": "en",
        "min_price": min_price_per_night,  # Minimum price per night
        # "max_price": max_price_per_night,  # Maximum price per night
        "sort_by": "3",  # Sort by lowest price
        "api_key": serpapi_api_key
    }

    search = GoogleSearch(params)
    results = search.get_dict()
    found_properties = results.get("properties", [])
    
    if not found_properties:
        return "No hotels found for the given destination and dates."
    
    cheapest_hotel = found_properties[0]
    cheapest_rate_per_night = cheapest_hotel.get("rate_per_night", {}).get("extracted_lowest", 0)
    
    if cheapest_rate_per_night > max_price_per_night:
        return "The budget is not enough for flight and hotel."
    
    most_expensive_affordable_hotel = None
    
    # Assuming hotels are sorted by price ascending
    for property in found_properties:
        price_per_night = property.get("rate_per_night", {}).get("extracted_lowest", 0)
        if price_per_night <= max_price_per_night:
            most_expensive_affordable_hotel = {
                "name": property.get("name"),
                "rate_per_night": price_per_night
            }
        else:
            break

    return most_expensive_affordable_hotel

    
    
    

def main():
    start_date_str, end_date_str, budget, trip_type = get_user_input()
    try:
        start_date, end_date, num_days = parse_dates(start_date_str, end_date_str)
        validate_dates(start_date, end_date)
        dest_suggestions = get_destination_suggestions(start_date, trip_type)
        print("Here are some suggested destinations for your trip:")
        print(dest_suggestions)
        
        # Dictionary to store destination data with flight prices
        destination_info = {}
        
        # Extract airport codes and destination names from destination suggestions
        for suggestion in dest_suggestions:
            airport_code, destination_name = suggestion.split(":")
            airport_code = airport_code.split()[-1]
            destination_info[airport_code] = {"destination_name": destination_name.strip()}

        # Get flight price insights and find the most expensive hotel for each destination
        for airport_code, info in destination_info.items():
            destination_name = info["destination_name"]
            
            # Get flight price insights
            flight_price = get_flight_price_insights("TLV", airport_code, start_date, end_date)
            if flight_price is not None:
                info["flight_price"] = flight_price
                
                # The hotel budget is the amount of money left after taking the cheepest flight
                hotel_budget = budget - flight_price
                # Find the most expensive hotel within the hotel budget
                hotel = get_most_expensive_hotel(destination_name, start_date, end_date, hotel_budget, num_days)
                if isinstance(hotel, dict):  # Check if the result is a dictionary
                    info["hotel_name"] = hotel["name"]
                    info["hotel_rate_per_night"] = hotel["rate_per_night"]
                else:
                    info["hotel_error"] = hotel  # Store the error message if it's not a dictionary
                
        
        
        # Print the destination details with the according flight price and hotel details
        print("Destination Details:")
        for index, (airport_code, info) in enumerate(destination_info.items(), start=1):
            destination_name = info["destination_name"]
            flight_price = info.get("flight_price", "N/A")
            hotel_name = info.get("hotel_name", "N/A")
            hotel_rate_per_night = info.get("hotel_rate_per_night", "N/A")
            hotel_error = info.get("hotel_error", None)  # Get the stored error message, if any
            total_price = flight_price + hotel_rate_per_night * num_days if flight_price != "N/A" and hotel_rate_per_night != "N/A" else "N/A"
            
            print(f"{index}. {destination_name} ({airport_code}):")
            print(f"  Flight Price: ${flight_price}")
            if hotel_error:
                print(f"  Hotel Error: {hotel_error}")  # Print the error message if it exists
                print()
            else:
                print(f"  Hotel Name: {hotel_name}")
                print(f"  Hotel Rate per Night: ${hotel_rate_per_night}")
                print(f"  Total Price: ${total_price}")
                print()
                
        # Allow the user to choose a destination
        chosen_index = int(input("Enter the number of your desired destination: "))
        if 1 <= chosen_index <= len(destination_info):
            chosen_destination = list(destination_info.values())[chosen_index - 1]
            chosen_destination_name = chosen_destination["destination_name"]
            flight_price = chosen_destination.get("flight_price", "N/A")
            hotel_rate_per_night = chosen_destination.get("hotel_rate_per_night", "N/A")
            total_price = flight_price + hotel_rate_per_night * num_days if flight_price != "N/A" and hotel_rate_per_night != "N/A" else "N/A"

            print(f"Chosen Destination: {chosen_destination_name}, Total Price: ${total_price}")
        else:
            print("Invalid choice. Please enter a valid number.")

             
             
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
