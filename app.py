import json
import aiohttp
import b_func 
from data import db_user,db_password,db_name,collection,db_read_ip
import asyncio
import random
from datetime import datetime, timedelta
import arrow
import time
import sys
from mail import send_custom_email
from sheet import send_sheet,read_data_sheet




if sys.version_info[0] == 3 and sys.version_info[1] >= 8 and sys.platform.startswith('win'):
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


file = open('discord.txt', 'r')
discord_tokens = [line.strip() for line in file]

async def authe():
    f = open("token.json")
    token = json.load(f)
    params = {
            'grant_type': 'refresh_token', 
            'client_id': 'f39df66e-633d-4b70-9a49-a8fd84db66fa',
            'refresh_token': token['refresh_token']
            }
    async with aiohttp.ClientSession() as session:
        status,_,_,response =await b_func.async_request_(session, 'https://login.live.com/oauth20_token.srf', 'POST', 'HTML', payload=params, proxy=None, auth_info=None, headers=None)
    _json = json.loads(response)
    with open("token.json", "w") as outfile:
        json.dump(_json, outfile)
    return {'Authorization': 'Bearer ' + _json['access_token']}

async def get_file(header,session,file_name,file_type):    
    url = 'https://graph.microsoft.com/v1.0/me/drive/root:' +'/NB Team FB 2022/Fulfillment/' + file_name +file_type+':/content'
    status,_,_,response =await b_func.async_request_(session, url, 'GET', "FILE", payload=None, proxy=None, auth_info=None, headers=header)
    if status in range(200, 202): return response
    elif file_type == '.png': return await get_file(header,session,file_name,'.jpg') 
    else: return []



async def convert_img(binary,session,sku):
    token_user = random.choice(discord_tokens)
    discord_header = {
        'authorization': token_user,
    }
    new = aiohttp.FormData()
    new.add_field('file',  binary,filename=f'{sku}.png',content_type='image/png')
    url = "https://discord.com/api/v9/channels/1029685295593033730/messages"
    status,_,_,res =  await b_func.async_request_(session,url, 'POST', 'FILE', payload=new, proxy=None, auth_info=None, headers=discord_header)
    while status not in range(200,203) :
        time.sleep(1)
        status,_,_,res =  await b_func.async_request_(session,url, 'POST', 'FILE', payload=new, proxy=None, auth_info=None, headers=discord_header)
        print(status)
    print(res['attachments'][0]['url'])
    return res['attachments'][0]['url']


async def do_gather_task1(order_info,session,agcm,time,header):
    send = True
    items = order_info['_original_data']['line_items']
    all_ = await asyncio.gather(*(do_gather_task2(item,order_info,session,header) for item in items ))
    update_ = []
    link = []
    result = {}
    for item in all_:
        if item != None :   
            update_.append([time,order_info['_original_data']['name'], item['sku'],item['title'],item['link'],item['design_name'],'Sent',item['note'],order_info['_original_data']['contact_email']])
            if item['link'] != None:
                link.append(item['link'])
            if item['note'] == 'Design not found':
                send = False
    if send and link !=[]:
        result['send_mail'] = [order_info['_original_data']['contact_email'],order_info['_original_data']['customer']['first_name'], 'mail_type',order_info['_original_data']['name'], time, link,order_info['_site']]
    else:
        for item in update_:
            item[6] = 'Not Sent'
    if update_ != []:
        result['sheet_data'] = update_
    return    result 

def gen_properties(properties):
    custom_name = []
    thumbnail = ''
    for properti in properties:
        if 'http' not in properti['value']:
            custom_name.append(properti['value']) 
        elif properti['name'] == 'thumbnail':
            thumbnail = properti['value']
    return custom_name,thumbnail




async def do_gather_task2(item,order_info,session,header):
    sku = item['sku']
    if sku:
        split_sku = sku.split('-')
        if len(split_sku) >5:
            product_type = split_sku[5]
            num = sku.index(product_type) +len(product_type)
            sku = sku[:num]
            note = ''
            link = ''
            design_name  = ''
            if product_type[-1] == 'c' :
                if item['properties']!= []:
                    custom_name,thumbnail = gen_properties(item['properties'])
                    if thumbnail != '':
                        file_name_custom = thumbnail.split('/')[-1]
                        design_name = order_info['_original_data']['name'][1:]+'-'+ sku + '-' +file_name_custom[:len(file_name_custom)-4]
                    else: 
                        if len(custom_name) >10: 
                            design_name = order_info['_original_data']['name'][1:]+'-'+ sku + '-' + custom_name[0][:10]
                        elif custom_name != []:
                            design_name = order_info['_original_data']['name'][1:]+'-'+ sku + '-' + custom_name[0]
                    print(design_name)        
                    check_esixt = await get_file(header,session,design_name,'.png')
                else:     
                    return 
            else:
                return
            if check_esixt != []: 
                link = await convert_img(check_esixt,session,sku)
            else:
                note = 'Design not found'
            new_line_item ={
                    'sku':item['sku'],
                    'title': item['title'],
                    'link':link,
                    'design_name':design_name,
                    'note': note
                }
            return new_line_item       
        else:pass    
    else:pass     


async def get_orders_info(time,agcm,header):
    db_host = random.choice(db_read_ip)
    async_db = b_func.db_itnit(db_user, db_password, db_host, db_name)
    d1 = f"{time}T00:00:01-07:00"
    start_time = arrow.get(d1).to('utc').datetime.replace(tzinfo=None)
    d2 = f"{time}T23:59:59-07:00"
    end_time = arrow.get(d2).to('utc').datetime.replace(tzinfo=None)
    date = {'$gte': start_time,'$lt': end_time}
    document_ = {
        '_original_data.created_at': date,
        '_site' :  {"$in":["getcus.com"]},
        '_original_data.line_items.fulfillment_status': {"$ne": "fulfilled"}    
        }
    filter = { 
        '_site': 1,
        '_original_data.contact_email': 1,
        '_original_data.customer.first_name': 1,
        '_original_data.created_at': 1,
        '_original_data.name': 1,
        '_original_data.line_items.id': 1,
        '_original_data.line_items.sku': 1,
        '_original_data.line_items.title': 1,
        '_original_data.line_items.properties': 1    
    }
    # filter = None
    orders_info = await b_func.do_find_many(async_db, collection, document_, filter)
    async with aiohttp.ClientSession() as session:
        # await do_gather_task1(orders_info[3],session,agcm,time,header)
        updates = await asyncio.gather(*(do_gather_task1(order_info,session,agcm,time,header) for order_info in orders_info)) 
        return [update for update in updates if update != {}]
    

async def main():
    header = await authe()
    twodays = (datetime.now() - timedelta(3)).strftime('%Y-%m-%d')
    orders =  await get_orders_info(twodays,'agcm',header)
    send_mail = [order['send_mail'] for order in orders if 'send_mail' in order]
    fails = send_custom_email(send_mail,'getcus.com')
    update_sheet = [order['sheet_data'] for order in orders if 'sheet_data' in order]
    flat_list = []
    for sublist in update_sheet:
        for item in sublist:
            print(item[1])
            if item[1] in fails:
                item[6] = 'Not Sent'
                item[7] = 'Server can not sent mail'
            flat_list.append(item)    
    send_sheet(flat_list)
    
def process_not_sent_mail():
    
    sheet_data = read_data_sheet()
    mails_not_send = [mail[1] for mail in sheet_data if mail[6] == 'Not Sent' ] 
    print(mails_not_send)

def job():
    asyncio.run(main())


def time_schedule():
    arrow_time = arrow.now('+07:00').format('HH:mm:ss')
    if arrow_time == '20:00:01':
        job()

# print('tool running')
# while True:
#     time_schedule()
#     time.sleep(1)
job()
# process_not_sent_mail()
