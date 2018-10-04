# NS - Hackathon 2017
# Dasitha Abeysinghe - dazimax@gmail.com
# Ajith Ranatunga - ajithkranatunga@gmail.com
# Tharindu Rajakaruna - tdr.open@gmail.com
# Irfan jamion - jamion.irfan@gmail.com
# Lakmal Demel - lakdemel@gmail.com

from xmlrpc import client
import json
import urllib.request
import urllib.parse
from pprint import pprint
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import hashlib

################################################
################################################
# Configurations
################################################

SKILL = 'MagVoice'
VERSION = '1.0.0'

MAGENTO_DOMAIN = 'm2domainname.com'
PROTOCOL = 'http://'
API_PATH = '/index.php/api/xmlrpc/'
API_USERNAME = '*******'
API_PASSWORD = '*******'
ENCRYPT_PASSWORD_SALT_KEY = ''
SYSTEM_EMAIL = '*******'

# Customer info
USER_FIRSTNAME = 'Dasitha'
USER_LASTNAME = 'Abeysinghe'
USER_EMAIL = '*******'
USER_PASSWORD = '*******'
USER_COMPANY = 'testCompany'
USER_STREET = 'testStreet'
USER_CITY = 'testCity'
USER_REGION = 'testRegion'
USER_POSTCODE = 'testPostcode'
USER_COUNTRY_ID = ''
USER_TELEPHONE = '*******'
USER_FAX = ''

# Credit card info & checkout
CC_CID = '*******'
CC_OWNER = '*******'
CC_NUMBER = '*******'
CC_TYPE = '*******'
CC_EXP_YEAR = '*******'
CC_MONTH = '*******'
CURRENCY_CODE = '*******'

# Category info
CATEGORY_LIST = ''

# Hunter API Configurations
HUNTER_API_KEY = '*******'
HUNTER_API_ENDPOINT = 'https://api.hunter.io/v2/domain-search?api_key=' + HUNTER_API_KEY + '&domain='

# Amazon SES Email API Configurations
EMAIL_HOST = '*******'
EMAIL_HOST_USER = '*******'
EMAIL_HOST_PASSWORD = '*******'
EMAIL_PORT = 587

# API Call
session = ''
client = client.ServerProxy(PROTOCOL + MAGENTO_DOMAIN + API_PATH, allow_none=True)
session = client.login(API_USERNAME, API_PASSWORD)
print('session id : ' + session)


# Alexa MagVoice Skill Integration
################################################
# Begin the Skill Script
################################################
def lambda_handler(event, context):
    if (event["session"]["application"]["applicationId"] !=
            "*******"):
        raise ValueError("Invalid Application ID")

    if event["session"]["new"]:
        on_session_started({"requestId": event["request"]["requestId"]}, event["session"])

    if event["request"]["type"] == "LaunchRequest":
        return on_launch(event["request"], event["session"])
    elif event["request"]["type"] == "IntentRequest":
        return on_intent(event["request"], event["session"])
    elif event["request"]["type"] == "SessionEndedRequest":
        return on_session_ended(event["request"], event["session"])


def on_launch(launch_request, alexa_session):
    return get_welcome_response()


def on_session_started(session_started_request, alexa_session):
    print("Starting new session.")


def on_session_ended(session_ended_request, alexa_session):
    print("Ending session.")
    # Cleanup goes here..
    card_title = "MagVoice - Thanks"
    speech_output = "Thank you for using the MagVoice. See you next time!"
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))


# Router Switch
def on_intent(intent_request, alexa_session):
    print('intent : ')
    pprint(intent_request)

    print('alexa_session : ')
    pprint(alexa_session)

    intent = intent_request["intent"]
    intent_name = intent_request["intent"]["name"]

    if intent_name == "GetCategories":
        return speech_get_category_list(intent, alexa_session)
    elif intent_name == "SendEnquery":
        return speech_send_customer_email(intent, alexa_session)
    elif intent_name == "GetProductList":
        return speech_get_product_list(intent, alexa_session)
    elif intent_name == "PlaceOrder":
        return speech_place_order(intent, alexa_session)
    elif intent_name == "LoadUser":
        return speech_load_user_details(intent, alexa_session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response()
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_cancel_request()
    elif intent_name == "GetCategory":
        return speech_get_category(intent, alexa_session)
    elif  intent_name == "setWebsite":
        return speech_select_website(intent, alexa_session)
    else:
        raise ValueError("Invalid intent")


################################################
################################################
# Define the custom functions

def get_welcome_response():
    session_attributes = {}
    card_title = "MagVoice"
    speech_output = "Welcome to the Alexa MagVoice. " \
                    "You can ask me for category listing," \
                    "product listing, make and enquery to customer support center or place an order on " + MAGENTO_DOMAIN + " E Commerce website."
    reprompt_text = "Please tell me your email to know whom I am talking with, " \
                    "for example my email is and after that password."
    should_end_session = False
    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def handle_session_cancel_request():
    card_title = "MagVoice - Thanks"
    speech_output = "Thank you for using the MagVoice. See you next time!"
    should_end_session = True

    return build_response({}, build_speechlet_response(card_title, speech_output, None, should_end_session))


################################################
# get_category_id_by_name
def get_category_id_by_name(category_name):
    # API CALL category list
    print('=============================================')
    print('API CAll : catalog_category.tree - level 0')
    response = client.call(session, 'catalog_category.tree')
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    # pprint(response_data['children'][0]['children'])

    category_level_array = response_data['children'][0]['children']
    category_id = ''
    for category in category_level_array:
        # print(category['name'])
        if category['name'].lower() == category_name.lower():
            category_id = category['category_id']
            print(category_id)
            print(category['name'])

    print('=============================================')
    return category_id


################################################
# get_product_info - get the product details info
def get_product_info(product_id):
    # API CALL for get product extra info
    print('=============================================')
    # Get product extra info
    # ------------------------------------
    print('API CAll : catalog_product.info')
    filter_array = [product_id]
    response = client.call(session, 'catalog_product.info', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    #print('product info : ')
    #print(response_data)

    return response_data


################################################
# get_product_image_info - get the product images
def get_product_image_info(product_id):
    # API CALL for get product image
    print('=============================================')
    # Get product image by sku
    # ------------------------------------
    print('API CAll : catalog_product_attribute_media.list')
    filter_array = [product_id]
    response = client.call(session, 'catalog_product_attribute_media.list', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    print('product image info : ')
    pprint(response_data)

    return response_data


################################################
# get_product_stock - get the product stock qty
def get_product_stock(product_sku):
    # API CALL for get product qty
    print('=============================================')
    # Get product qty by sku
    # ------------------------------------
    print('API CAll : product_stock.list')
    filter_array = [product_sku]
    response = client.call(session, 'product_stock.list', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    #print('product stock : ')
    #pprint(response_data)

    return response_data


################################################
# get_product_details_list - get the product list with details
def get_product_details_list(category_name):
    # API CALL for get product list
    print('=============================================')
    # Get product list by category name
    # ------------------------------------
    print('API CAll : catalog_product.list')
    filter_array = [{}]
    response = client.call(session, 'catalog_product.list', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    print('category products count : ')
    product_count = len(response_data)
    pprint(product_count)
    # pprint(response_data)

    cateegory_id = get_category_id_by_name(category_name)
    category_products = []
    selected_product_attributes = []

    # get category products, qty check and add product info
    # get only top 5 products
    product_counter = 0
    if cateegory_id != '':

        for product in response_data:
            if cateegory_id in product['category_ids']:

                if product_counter == 5:
                    break

                print(product)
                product_info = get_product_info(product['product_id'])
                product_stock_details = get_product_stock(product['sku'])
                product_image_info = get_product_image_info(product['product_id'])

                # add product to array
                # print('stock : ')
                # print(product_stock_details[0]['is_in_stock'])
                # print('qty : ')
                # print(product_stock_details[0]['qty'])
                if product_stock_details[0]['is_in_stock'] == '1':

                    if len(product) > 0:
                        append_product_id = product['product_id']
                    else:
                        append_product_id = ''
                    if len(product) > 0:
                        append_sku = product['sku']
                    else:
                        append_sku = ''
                    if len(product) > 0:
                        append_name = product['name']
                    else:
                        append_name = ''
                    if len(product_info) > 0:
                        append_description = product_info['description']
                    else:
                        append_description = ''
                    if len(product_info) > 0:
                        append_price = CURRENCY_CODE + ' ' + '%.2f' % float(product_info['price'])
                    else:
                        append_price = ''
                    if len(product_stock_details) > 0:
                        append_qty = int(float(product_stock_details[0]['qty']))
                    else:
                        append_qty = ''
                    if len(product_image_info) > 0:
                        append_image_url = product_image_info[0]['url']
                    else:
                        append_image_url = ''
                    if len(product_info) > 0:
                        append_product_url = PROTOCOL + MAGENTO_DOMAIN + '/' + product_info['url_path']
                    else:
                        append_product_url = ''

                    # add product attribute to array
                    category_products.append({
                        "product_id": append_product_id,
                        "sku": append_sku,
                        "name": append_name,
                        "description": append_description,
                        "price": append_price,
                        "qty": append_qty,
                        "image_url": append_image_url,
                        "product_url": append_product_url,
                    })

                    # add limitation
                    product_counter += 1
    else:
        print('category id not found for ' + category_name)

    # print('available product info array : ')
    # pprint(category_products)
    return category_products


################################################
# get_country_id - get country id by country name
def get_country_id(countryname):
    # API CALL for get country id
    print('=============================================')
    # Get country id by country name
    # ------------------------------------
    print('API CAll : country.list')
    response = client.call(session, 'country.list')
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    country_id = ''
    for country in response_data:
        # print(country['name'].lower())
        if country['name'].lower() == countryname:
            country_id = country['country_id']
    # print('country id : '+country_id)
    # pprint(response_data)
    return country_id


################################################
# is_exists_customer - check customer account exists
def is_exists_customer(email):
    # API CALL for check customer exists
    print('=============================================')
    # Check customer exists or not
    # ------------------------------------
    print('API CAll : customer.list')
    filter_array = [{
        'email': email
    }]
    response = client.call(session, 'customer.list', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)
    # pprint(response_data)

    if len(response_data) > 0:
        return True
    else:
        return False


################################################
# is_valid_customer - check customer account is valid or not
def is_valid_customer(email, password):
    # API CALL for get customer details
    print('=============================================')
    # Get customer details for validate the account
    # ------------------------------------
    print('API CAll : customer.list')
    filter_array = [{
        'email': email
    }]
    response = client.call(session, 'customer.list', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    db_password_array = response_data[0]['password_hash']
    password_info = db_password_array.split(':')
    db_password_hash = password_info[0]
    ENCRYPT_PASSWORD_SALT_KEY = password_info[1]

    create_hash_password = ENCRYPT_PASSWORD_SALT_KEY + password
    hash_password = hashlib.md5(create_hash_password.encode()).hexdigest()

    if db_password_hash == hash_password:
        print(
            'valid user logins for : ' + email + ' : db_password_hash ' + db_password_hash + ' hash_password : ' + hash_password)
        return True
    else:
        print('wrong user loggins for : ' + email + ' password : ' + password)
        return False

        # pprint(response_data)


################################################
# get_customer_details - load the customer details
def get_customer_details(email):
    # API CALL for get customer details
    print('=============================================')
    # Get customer details
    # ------------------------------------
    print('API CAll : customer.list')
    filter_array = [{
        'email': email
    }]
    response = client.call(session, 'customer.list', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)
    return response_data


################################################
# create_customer - create the customer
def create_customer():
    # API CALL for create customer
    print('=============================================')
    # Create customer
    # ------------------------------------
    print('API CAll : customer.create')
    filter_array = [{
        'email': USER_EMAIL,
        'firstname': USER_FIRSTNAME,
        'lastname': USER_LASTNAME,
        'password': USER_PASSWORD,
        'website_id': '1',
        'store_id': '1',
        'group_id': '1'
    }]
    response = client.call(session, 'customer.create', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)
    # pprint(response_data)

    customer_id = response_data
    return customer_id


################################################
# get_credit_card_type - get the credit card type
def get_credit_card_type(cardtype):
    cardtypeid = ''
    if cardtype.lower() == 'visa':
        cardtypeid = 'VI'
    if cardtype.lower() == 'american express':
        cardtypeid = 'AE'
    if cardtype.lower() == 'master':
        cardtypeid = 'MC'
    if cardtype.lower() == 'discover':
        cardtypeid = 'DI'

    return cardtypeid


################################################
# place_order - create the order
def place_order(product_id):
    print('=============================================')
    # check customer is registered if not create new customer account
    # ------------------------------------
    #USER_COUNTRY_ID = get_country_id('australia')
    USER_COUNTRY_ID = 'AU'
    print('USER_COUNTRY_ID : ' + USER_COUNTRY_ID)

    customer_info = get_customer_details(USER_EMAIL)
    # print('customer info : ')
    # pprint(customer_info)
    #print('customer id : ' + customer_info[0]['customer_id'])

    if len(customer_info) < 1:
        create_customer()

    # API CALL place order
    print('=============================================')
    # Create a quote, get quote identifier
    # ------------------------------------
    print('API CAll : cart.create')
    response = client.call(session, 'cart.create')
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    shopping_cart_id = response_data

    # Set customer for example guest
    # ------------------------------------
    print('API CAll : cart_customer.set')
    # filter_array = [shopping_cart_id,{
    #    'firstname': USER_FIRSTNAME,
    #    'lastname': USER_LASTNAME,
    #   'email': USER_EMAIL,
    #    'website_id': '1',
    #    'store_id': '1',
    #    'group_id': '1',
    #    'mode': 'guest'
    # }]

    filter_array = [shopping_cart_id, {
        'entity_id': customer_info[0]['customer_id'],
        'mode': 'customer'
    }]

    response = client.call(session, 'cart_customer.set', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    is_customer_set_to_cart = response_data

    #print('customer details : ')
    #for customer in filter_array:
    #    pprint(customer)

    # Set customer addresses for example guest's addresses
    # ------------------------------------
    print('API CAll : cart_customer.addresses')

    filter_array = [shopping_cart_id, [{
        'mode': 'shipping',
        'firstname': USER_FIRSTNAME,
        'lastname': USER_LASTNAME,
        'email': USER_EMAIL,
        'company': USER_COMPANY,
        'street': USER_STREET,
        'city': USER_CITY,
        'region': USER_REGION,
        'postcode': USER_POSTCODE,
        'country_id': USER_COUNTRY_ID,
        'telephone': USER_TELEPHONE,
        'fax': USER_FAX,
        'is_default_shipping': '0',
        'is_default_billing': '0'
    }
        , {
            'mode': 'billing',
            'firstname': USER_FIRSTNAME,
            'lastname': USER_LASTNAME,
            'email': USER_EMAIL,
            'company': USER_COMPANY,
            'street': USER_STREET,
            'city': USER_CITY,
            'region': USER_REGION,
            'postcode': USER_POSTCODE,
            'country_id': USER_COUNTRY_ID,
            'telephone': USER_TELEPHONE,
            'fax': USER_FAX,
            'is_default_shipping': '0',
            'is_default_billing': '0'
        }]
                    ]
    response = client.call(session, 'cart_customer.addresses', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    is_customer_address_set_to_cart = response_data

    # add products into shopping cart
    # ------------------------------------
    print('API CAll : cart_product.add')
    print('product id : ')
    print(product_id)
    filter_array = [shopping_cart_id, [{
        'product_id': product_id,
        'qty': 1
    }]]
    response = client.call(session, 'cart_product.add', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    #print('response_data : ')
    #pprint(response_data)

    is_product_add_to_cart = response_data

    #print('added products : ')
    #for product in filter_array:
    #    pprint(product)

    # update product in shopping cart
    # ------------------------------------
    # print('API CAll : cart_product.update')
    # filter_array = [shopping_cart_id, [{
    #    'product_id': '1',
    #    'qty': '2'
    # }]]
    # response = client.call(session, 'cart_product.update', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    # encode_response = json.dumps(response)
    # response_data = json.loads(encode_response)

    # is_product_update_at_cart = response_data

    # remove products from shopping cart, for example by SKU
    # ------------------------------------
    # print('API CAll : cart_product.remove')
    # filter_array = [shopping_cart_id, [{
    #    'sku': '1231'
    # }]]
    # response = client.call(session, 'cart_product.remove', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    # encode_response = json.dumps(response)
    # response_data = json.loads(encode_response)

    # is_product_remove_from_cart = response_data

    # get list of products
    # ------------------------------------
    # print('API CAll : cart_product.list')
    # response = client.call(session, 'cart_product.list', [shopping_cart_id])
    # response coming from json for the confirmation re-encode to json and decode
    # encode_response = json.dumps(response)
    # response_data = json.loads(encode_response)

    # cart_product_list = response_data

    # get list of shipping methods
    # ------------------------------------
    print('API CAll : cart_shipping.list')
    filter_array = [shopping_cart_id]
    response = client.call(session, 'cart_shipping.list', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    available_shipping_methods = response_data

    # only support for freeshipping_freeshipping & flatrate_flatrate
    #shipping_method = ''
    #shipping_array = []
    #for shipping_method in available_shipping_methods:
        # print(shipping_method['code'])
        #shipping_array.append(shipping_method['code'])

    #if 'freeshipping_freeshipping' in shipping_array:
    #    shipping_method = 'freeshipping_freeshipping'

    #if 'flatrate_flatrate' in shipping_array:
    #    if shipping_method == '':
    #        shipping_method = 'flatrate_flatrate'

    #if shipping_method == '':
    #    print('Free Shipping or Flat Rate shipping method should be enable to proceed checkout.')

    #print('shipping_method : ')
    #print(shipping_method)

    shipping_method = 'freeshipping_freeshipping'

    # set shipping method
    # ------------------------------------
    print('API CAll : cart_shipping.method')
    filter_array = [shopping_cart_id, shipping_method]
    response = client.call(session, 'cart_shipping.method', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    is_shipping_method_set = response_data

    print('is_shipping_method_set : ')
    print(is_shipping_method_set)

    # get list of payment methods
    # ------------------------------------
    #print('API CAll : cart_payment.list')
    #filter_array = [shopping_cart_id]
    #response = client.call(session, 'cart_payment.list', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    #encode_response = json.dumps(response)
    #response_data = json.loads(encode_response)

    #available_payment_methods = response_data

    # only support for ccsave & checkmo
    #payment_method = ''
    #payment_array = []
    #for payment_method in available_payment_methods:
        # print(payment_method['code'])
    #    payment_array.append(payment_method['code'])

    #if 'checkmo' in payment_array:
    #    payment_method = 'checkmo'

    #if 'cod' in payment_array:
    #    if payment_method == '':
    #        payment_method = 'cod'

    # if 'ccsave' in payment_array:
    #    if payment_method == '':
    #        payment_method = 'ccsave'

    #if payment_method == '':
    #    print('Free Shipping or Flat Rate shipping method should be enable to proceed checkout.')

    payment_method = 'checkmo'
    print('payment_method : ' + payment_method)

    # set payment method
    # ------------------------------------
    print('API CAll : cart_payment.method')

    #if payment_method == 'checkmo':
    #    filter_array = [shopping_cart_id, {
    #        'method': payment_method
    #    }]

    #if payment_method == 'cod':
    #    filter_array = [shopping_cart_id, {
    #        'method': payment_method
    #    }]

    filter_array = [shopping_cart_id, {
        'method': payment_method
    }]

        # if payment_method == 'ccsave':
        # need to disable the SavedCC payment method Request Card Security Code in website configurations
        #    CC_TYPE = get_credit_card_type('visa')

        #   filter_array = [shopping_cart_id,{
        #       'method': payment_method,
        #       'cc_cid': CC_CID,
        #       'cc_owner': CC_OWNER,
        #       'cc_number': CC_NUMBER,
        #       'cc_type': CC_TYPE,
        #       'cc_exp_year': CC_EXP_YEAR,
        #       'cc_exp_month': CC_MONTH
        #   }]

    response = client.call(session, 'cart_payment.method', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    is_payment_method_set = response_data

    # add coupon
    # ------------------------------------
    # print('API CAll : cart_coupon.add')
    # coupon_code = 'aCouponCode'
    # filter_array = [shopping_cart_id, coupon_code]
    # response = client.call(session, 'cart_coupon.add', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    # encode_response = json.dumps(response)
    # response_data = json.loads(encode_response)

    # is_coupon_code_set = response_data

    # remove coupon
    # ------------------------------------
    # print('API CAll : cart_coupon.remove')
    # filter_array = [shopping_cart_id]
    # response = client.call(session, 'cart_coupon.remove', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    # encode_response = json.dumps(response)
    # response_data = json.loads(encode_response)

    # is_coupon_removed = response_data

    # get total prices
    # ------------------------------------
    # print('API CAll : cart.totals')
    # filter_array = [shopping_cart_id]
    # response = client.call(session, 'cart.totals', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    # encode_response = json.dumps(response)
    # response_data = json.loads(encode_response)

    # cart_totals_details = response_data

    # get full information about shopping cart
    # ------------------------------------
    print('API CAll : cart.info')
    filter_array = [shopping_cart_id]
    response = client.call(session, 'cart.info', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    cart_info_details = response_data
    #pprint(cart_info_details)

    # get list of licenses
    # ------------------------------------
    # print('API CAll : cart.licenseAgreement')
    # filter_array = [shopping_cart_id]
    # response = client.call(session, 'cart.licenseAgreement', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    # encode_response = json.dumps(response)
    # response_data = json.loads(encode_response)

    # cart_info_details = response_data

    # create order
    # ------------------------------------
    print('API CAll : cart.order')
    filter_array = [shopping_cart_id]
    response = client.call(session, 'cart.order', filter_array)
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    order_id = response_data
    print('order id : ' + order_id)

    #pprint(response_data)

    print('=============================================')
    return order_id


################################################
# get_last_order_details
def get_last_order_details():
    session_attributes = {}
    card_title = SKILL + " Get Last Order Details"
    reprompt_text = ""
    should_end_session = False

    # API CALL last order details
    print('=============================================')
    print('API CAll : sales_order.list - last order details')

    filter_array = [{'customer_email': USER_EMAIL}]
    response = client.call(session, 'sales_order.list', filter_array)

    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    print('=============================================')

    # response generate
    speech_output = ''
    if (len(response_data) > 0):
        last_order_index = len(response_data) - 1
        # pprint(response_data[last_order_index])
        order_id = response_data[last_order_index]['increment_id']
        order_state = response_data[last_order_index]['state']
        order_status = response_data[last_order_index]['status']

        speech_output += 'Your order id ' + order_id + ' current state is ' + order_state + ' and status ' + order_status
        speech_output += ". Are there anything I can help you with " + USER_FIRSTNAME + "?"
    else:
        speech_output += 'Sorry at this movement there have no order placed for your email ' + USER_EMAIL
        speech_output += ". Are there anything I can help you with " + USER_FIRSTNAME + "?"

    print('response : ' + speech_output)

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


def send_customer_enquery(website, email_subject, email_body):
    if website == '':
        print('Please add support require website domain name')
    elif email_subject == '':
        print('Please add subject to email')
    elif email_body == '':
        print('Please add email content')

    support_email_response = get_website_support_email(website)
    support_name = support_email_response['emailname']
    support_email = support_email_response['email']

    print('support_email : ')
    pprint(support_email)

    # hard coded for demostrations
    support_email = '***********'
    USER_EMAIL = '***********'

    status = send_email(USER_EMAIL, support_email, email_subject, email_body)
    return status


################################################
################################################
# MageVoice system functions

def get_website_support_email(domain):
    hunter_request = HUNTER_API_ENDPOINT + domain
    email_response = urllib.request.urlopen(hunter_request)
    email_data = email_response.read()
    email_encoding = email_response.info().get_content_charset('utf-8')
    response_data = json.loads(email_data.decode(email_encoding))

    supportEmail = ''
    supportName = ''
    for email in response_data['data']['emails']:
        emailname = email['value'].split('@')
        if emailname[0] == 'support':
            supportEmail = email['value']
            supportName = emailname[0]
        elif emailname[0] == 'enquries':
            supportEmail = email['value']
            supportName = emailname[0]
        elif emailname[0] == 'info':
            supportEmail = email['value']
            supportName = emailname[0]
        elif emailname[0] == 'contact':
            supportEmail = email['value']
            supportName = emailname[0]
        elif supportEmail == '':
            supportEmail = email['value']
            supportName = emailname[0]

    emailInfo = {'emailname': supportName, 'email': supportEmail}
    return emailInfo


def send_email(from_email, to_email, subject, email_body):
    if from_email == '':
        print('Please add from email')
    elif to_email == '':
        print('Please add to email')
    elif subject == '':
        print('Please add subject of the email')
    elif email_body == '':
        print('Please add email body')

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = to_email

    html = email_body

    mime_text = MIMEText(html, 'html')
    msg.attach(mime_text)

    s = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
    s.starttls()
    s.login(EMAIL_HOST_USER, EMAIL_HOST_PASSWORD)
    s.sendmail(msg['From'], msg['To'], msg.as_string())
    s.quit()

    print('email sent..')
    return True


################################################

################################################
# speech_load_user_details
def speech_load_user_details(intent, alexa_session):
    session_attributes = {}
    card_title = SKILL + " Load User details"
    reprompt_text = "Sorry, I didn't understand. Please try again."
    should_end_session = False

    speech_output = ''
    customer_email = ''
    customer_password = ''

    print('slots : ')
    pprint(intent['slots'])

    if 'CustomerEmail' in intent['slots']:
        if 'value' in intent['slots']['CustomerEmail']:
            customer_email = intent['slots']['CustomerEmail']['value']

    if 'CustomerPassword' in intent['slots']:
        if 'value' in intent['slots']['CustomerPassword']:
            customer_password = intent['slots']['CustomerPassword']['value']

    if customer_email != '' and customer_password != '':
        is_valid = is_valid_customer(customer_email, customer_password)
        if is_valid:
            customer_info = get_customer_details(customer_email)
            print('customer_info')
            pprint(customer_info)

            if 'first_name' in customer_info:
                USER_FIRSTNAME = customer_info['first_name']
            if 'last_name' in customer_info:
                USER_LASTNAME = customer_info['last_name']
            if 'email' in customer_info:
                USER_EMAIL = customer_info['email']
            if 'password_hash' in customer_info:
                USER_PASSWORD = customer_password
            if 'company' in customer_info:
                USER_COMPANY = customer_info['company']
            if 'street' in customer_info:
                USER_STREET = customer_info['street']
            if 'city' in customer_info:
                USER_CITY = customer_info['city']
            if 'region' in customer_info:
                USER_REGION = customer_info['region']
            if 'postcode' in customer_info:
                USER_POSTCODE = customer_info['postcode']
            if 'country_id' in customer_info:
                USER_COUNTRY_ID = customer_info['country_id']
            if 'telephone' in customer_info:
                USER_TELEPHONE = customer_info['telephone']
            if 'fax' in customer_info:
                USER_FAX = customer_info['fax']

        else:
            speech_output = 'Sorry I could not validated your email on ' + MAGENTO_DOMAIN
            speech_output += 'At the movement I am only supported to this' + MAGENTO_DOMAIN + '. So before proceed you may need to register'
            speech_output += 'with this E Commerce website or try again.'
    else:
        speech_output = 'Sorry I could not validated your email on ' + MAGENTO_DOMAIN
        speech_output += 'At the movement I am only supported to this' + MAGENTO_DOMAIN + '. So before proceed you may need to register'
        speech_output += 'with this E Commerce website or try again.'

    print('=============================================')

    print('response : ' + speech_output)

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


################################################
# speech_place_order
def speech_place_order(intent, alexa_session):
    session_attributes = {}
    card_title = SKILL + " Place Order"
    reprompt_text = "Sorry, I didn't understand. Please try again."
    should_end_session = False

    speech_output = ''
    product_id = ''
    order_id = ''

    print('slots : ')
    pprint(intent['slots'])

    if 'ProductId' in intent['slots']:
        if 'value' in intent['slots']['ProductId']:
            product_id = intent['slots']['ProductId']['value']

            if product_id != '':
                order_id = place_order(product_id)
    else:
        speech_output = 'Sorry I could not place the order without product id.'
        speech_output += 'Please try again.'

    print('=============================================')

    # response generate
    if order_id != '':
        speech_output = USER_FIRSTNAME + ' You have succesfully placed order at ' + MAGENTO_DOMAIN
        speech_output += " Your order id is " + order_id
        speech_output += " You wil receive an email from the " + MAGENTO_DOMAIN + " shortly."
        speech_output += " Are there anything I can help you with " + USER_FIRSTNAME + "?"

    else:
        speech_output = "Sorry, I could not place the order due to some unknown issue."
        speech_output += " I would suggest to contact their support and make an inquery regarding this."
        speech_output += " Are there anything I can help you with " + USER_FIRSTNAME + "?"

    print('response : ' + speech_output)

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


################################################
# speech_get_product_list - load top 5 product list by category name
def speech_get_product_list(intent, alexa_session):
    session_attributes = {}
    card_title = SKILL + " Get Product List"
    reprompt_text = "Sorry, I didn't understand. Please try again."
    should_end_session = False

    speech_output = ''
    category_name = ''
    available_products = []
    email_body = ''
    email_subject = 'Alexa MagVoice - ' + MAGENTO_DOMAIN + ' Searched Product List'

    print('slots : ')
    pprint(intent['slots'])

    if 'CategoryName' in intent['slots']:
        if 'value' in intent['slots']['CategoryName']:
            category_name = intent['slots']['CategoryName']['value']

    print('category_name before filter : ' + category_name)

    # alexa will pickup sentense some times needs to filter it
    if category_name != '':
        if ' ' in category_name:
            search_category_name = category_name.split(' ')
            print('search_category_name len : ')
            pprint(len(search_category_name))
            category_last_word_count = len(search_category_name) - 1
            print('search_category_name last word count : ')
            print(category_last_word_count)
            category_name = search_category_name[category_last_word_count]

    print('category_name : ' + category_name)

    if category_name != '':
        available_products = get_product_details_list(category_name)
        print('available_products : ')
        pprint(available_products)

        # response generate
        if len(available_products) > 0:
            email_body = '<p>Hi ' + USER_FIRSTNAME + ',</p><br/>'
            email_body += '<p>' + MAGENTO_DOMAIN + " currently listed top products are, </p>"
            email_body += '<ul>'

            for product in available_products:

                email_body += '<li style="list-style:none;"><div><a href=' + product['product_url'] + '>'
                email_body += '<img src=' + product['image_url'] + '/><br/></a>'
                email_body += '<a href=' + product['product_url'] + '>' + product['name'] + '</a><br/>'
                email_body += 'Price : ' + product['price'] + ' <br/>'
                email_body += '<b>Product ID : ' + product['product_id'] + '</b> <br/>'
                email_body += 'Description : ' + product['description'] + ' <br/>'
                email_body += '</div></li>'

            email_body += '</ul>'
        else:
            speech_output = "Sorry, I could not find any products related to " + category_name + " category on " + MAGENTO_DOMAIN + " at the movement."
            speech_output += " I would suggest to contact their support and make an inquery regarding this."
            speech_output += " Are there anything I can help you with " + USER_FIRSTNAME + "?"

        print('==================================')
        status = send_email(SYSTEM_EMAIL, USER_EMAIL, email_subject, email_body)

        if status == True:
            speech_output = 'Ok ' + USER_FIRSTNAME + ', I sent you an email with top products listing. '
            speech_output += 'Please check those products and '
            speech_output += 'tell me the selected product id to place the order.'

        print('email_body :')
        pprint(email_body)
        print('response : ' + speech_output)

    else:
        speech_output = 'Sorry I could not provide you product list items without a category name.'
        speech_output += 'Please try again.'

    print('=============================================')

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


################################################
# speech_get_category_list - load all the magento category level one list
def speech_get_category_list(intent, alexa_session):
    session_attributes = {}
    card_title = SKILL + " Get Category List"
    reprompt_text = "Sorry, I didn't understand. Please try again."
    should_end_session = False

    category_level_one_list = {}
    response = ''
    encode_response = ''
    response_data = ''

    # API CALL category list
    print('=============================================')
    print('API CAll : catalog_category.tree - level 0')
    response = client.call(session, 'catalog_category.tree')
    # response coming from json for the confirmation re-encode to json and decode
    encode_response = json.dumps(response)
    response_data = json.loads(encode_response)

    category_level_array = response_data['children'][0]['children']
    CATEGORY_LIST = category_level_array
    # print(categoryLevel0Array)

    for category in category_level_array:
        print(category['name'])
    print('=============================================')

    # response generate
    if len(category_level_array) > 0:
        speech_output = MAGENTO_DOMAIN + " currently listed categories are "
        for category in category_level_array:
            speech_output += category['name'] + ', '
        speech_output = speech_output.rstrip(' ,\n')
    else:
        speech_output = "Sorry, I could'n find any category listed on " + MAGENTO_DOMAIN + " at the movement."
        speech_output += " I would suggest to contact their support and make an inquery regarding this."
        speech_output += " Are there anything I can help you with " + USER_FIRSTNAME + "?"

    print('response : ' + speech_output)

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


################################################
# speech - speech_send_customer_email
def speech_send_customer_email(intent, alexa_session):
    session_attributes = {}
    card_title = SKILL + " Send Customer Enquery"
    reprompt_text = "Sorry, I didn't understand. Please try again."
    should_end_session = False

    speech_output = ""
    email_website = ''

    print('slots : ')
    pprint(intent['slots'])

    if 'EmailSubject' in intent['slots']:
        if 'value' in intent['slots']['EmailSubject']:
            email_subject = intent['slots']['EmailSubject']['value']

    if 'EmailBody' in intent['slots']:
        if 'value' in intent['slots']['EmailBody']:
            email_body = intent['slots']['EmailBody']['value']

    if 'EmailWebsite' in intent['slots']:
        if 'value' in intent['slots']['EmailWebsite']:
            email_website = intent['slots']['EmailWebsite']['value']

    email_subject = 'Customer Enquiry - Regarding Product Catalogues'
    email_body = '<p>Hi,<br/>I want to need some details regarding your product catalogues. '
    email_body += 'Please call me back ' + USER_TELEPHONE + ' or email me ' + USER_EMAIL + ' soon.</p><br/>'
    email_body += 'Best regards,<br/>'
    email_body += USER_FIRSTNAME

    print('email_subject : ')
    pprint(email_subject)

    print('email_body : ')
    pprint(email_body)

    print('email_website : ')
    pprint(email_website)

    status = send_customer_enquery(email_website, email_subject, email_body)

    if status == True:
        speech_output = 'Enquery email successfully sent!'
    else:
        speech_output = 'Enquery email sent faild!'

    return build_response(session_attributes, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))


################################################
################################################
# Dynamo DB Integration functions


################################################
################################################
# Alexa Voice API functions

def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        "outputSpeech": {
            "type": "PlainText",
            "text": output
        },
        "card": {
            "type": "Simple",
            "title": title,
            "content": output
        },
        "reprompt": {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt_text
            }
        },
        "shouldEndSession": should_end_session
    }


def build_response(session_attributes, speechlet_response):
    return {
        "version": "1.0",
        "sessionAttributes": session_attributes,
        "response": speechlet_response
    }

################################################
# Find website
################################################

################################################

def getCategoryOf(index):
    if index in ["cloths","Cloth", "Cloth"]:
        return "bundabergrum"
    if index == "cloth":
        return "bundabergrum"
    else:
        return False

################################################

def getWesites(index):
    if index in ["bundabergrum","Bundabergrum", "bundaber grum"]:
        MAGENTO_DOMAIN = '***********'
        return "bundabergrum"
    if index == "bundabergrum":
        MAGENTO_DOMAIN = '***********'
        return "bundabergrum"
    else:
        return False


################################################
# speech_select_website - load all the magento site based on category
def speech_select_website(intent, alexa_session):
    session_attributes = {}
    card_title = SKILL + " Select website"
    reprompt_text = "Sorry, I didn't understand. Please try again."
    should_end_session = False

    if 'Website' in intent['slots']:
        if 'value' in intent['slots']['Website']:
            website_name = intent['slots']['Website']['value']
            if getWesites(website_name):
                speech_output = "you have select " + website_name + "web site"
                return build_response(session_attributes, build_speechlet_response(
                    card_title, speech_output, reprompt_text, should_end_session))

    return build_response(session_attributes, build_speechlet_response(
        card_title, "Please try again", reprompt_text, should_end_session))

################################################


################################################
# speech_get_category - load all the magento site based on category
def speech_get_category(intent, alexa_session):
    session_attributes = {}
    card_title = SKILL + " Get Category and list website"
    reprompt_text = "Sorry, I didn't understand. Please try again."
    should_end_session = False

    category_level_one_list = {}
    print("CategoryName display")
    print(intent['slots'])
    if 'Category' in intent['slots']:
        print("CategoryName display 1")
        if 'value' in intent['slots']['Category']:
            print("CategoryName display 2")
            category_name = intent['slots']['Category']['value']
            print(category_name)
            print(getCategoryOf(category_name))
            if getCategoryOf(category_name):
                print("CategoryName display 3")
                print("working")
                speech_output = "we have " + category_name +"on" + getCategoryOf(category_name) + " what do you prefer"
                return build_response(session_attributes, build_speechlet_response(
                    card_title, speech_output, reprompt_text, should_end_session))

    return build_response(session_attributes, build_speechlet_response(
        card_title, "Please try again", reprompt_text, should_end_session))


################################################
# End Skill Script
################################################

