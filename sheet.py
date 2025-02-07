from googleapiclient import discovery
from google.oauth2.service_account import Credentials
from pprint import pprint
import string

def get_creds():
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html#for-bots-using-service-account
    creds = Credentials.from_service_account_file("vertical-vault-341807-2315c66efdf5.json")
    scoped = creds.with_scopes([
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ])
    return scoped


def send_sheet(data):
    service = discovery.build('sheets', 'v4', credentials=get_creds())
    spreadsheet_id = '159Jh5jNQdFcYj9v51rAt0gFfvTA7FBI9hq3GZhcoENg'
    range_ = "Preview cases"
    value_input_option = "USER_ENTERED"
    value_range_body = {"values": data}
    request = service.spreadsheets().values().append(spreadsheetId=spreadsheet_id, range=range_, valueInputOption=value_input_option,insertDataOption='INSERT_ROWS', body=value_range_body)
    response = request.execute()
    pprint(response)

def read_data_sheet():
    service = discovery.build('sheets', 'v4', credentials=get_creds())
    spreadsheet_id = '159Jh5jNQdFcYj9v51rAt0gFfvTA7FBI9hq3GZhcoENg'
    range_ = "Preview cases"
    request = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id,range=range_)                           
    response = request.execute()
    return response.get('values',[])

def batch_update_values(ranges,updates):     
    print(ranges,updates)     
    service = discovery.build('sheets', 'v4', credentials=get_creds())
    spreadsheet_id = '159Jh5jNQdFcYj9v51rAt0gFfvTA7FBI9hq3GZhcoENg'
    data = []
    for i,range_ in enumerate(ranges):
        json_ = {
            'range': range_,
            'values': [updates[i]]
        }
        data.append(json_)
    body = {
        'valueInputOption': "USER_ENTERED",
        'data': data
    }
    result = service.spreadsheets().values().batchUpdate(
        spreadsheetId=spreadsheet_id, body=body).execute()
    print(f"{(result.get('totalUpdatedCells'))} cells updated.")
    return result
    
def updates_data(original_data,update_):
    columns = list(string.ascii_uppercase)
    ranges = []
    sheet_updates = []
    sheetname = 'Preview cases'
    for i,data in enumerate(original_data):
        for update in update_:
            if data[0] == update[0]:
                range_ =f'{sheetname}!A{i+1}:{columns[len(update)-1]}{i+1}'
                ranges.append(range_)
                sheet_updates.append(update)
    batch_update_values(ranges,sheet_updates)
    