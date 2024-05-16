import requests
import datetime

# Set up OpenAI API credentials
openai_api_key = "sk-proj-wQ4taTDDFhbuDrmkqIlOT3BlbkFJlJVo8Zlx0wucOcJ2atou"
openai_api_model = "gpt-3.5-turbo"

def get_user_input():
    start_date_str = input("Enter the start date of your trip (YYYY-MM-DD): ")
    end_date_str = input("Enter the end date of your trip (YYYY-MM-DD): ")
    budget = input("Enter your total budget in USD for the trip: ")
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
    

def main():
    start_date_str, end_date_str, budget, trip_type = get_user_input()
    try:
        start_date, end_date, num_days = parse_dates(start_date_str, end_date_str)
        validate_dates(start_date, end_date)
        suggestions = get_destination_suggestions(start_date, trip_type)
        print("Here are some suggested destinations for your trip:")
        print(suggestions)
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
