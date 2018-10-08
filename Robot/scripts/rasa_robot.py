# coding: utf-8
from rasa_nlu.model import Interpreter
from random import choice, random
from time import localtime, sleep
from requests import get
from bs4 import BeautifulSoup
from collections import namedtuple
from warnings import filterwarnings
import sqlite3 as sql

filterwarnings('ignore')

JOKE_ADDR = 'https://www.qiushibaike.com/text/'
STOCK_ADDR = 'http://hq.sinajs.cn/list=%s%s'
STOCK_FORMAT = ['Name', 'Open', 'High', 'Low', 'Current', 'volume']
NEWS_ADDR = 'http://search.sina.com.cn/?q=%s&range=all&c=news&sort=time'
NEWS_FORMAT = namedtuple('news', ['Keyword', 'Title', 'Link'])

RESPONSE_GREET = ['Hello, my friend!', 'Good to see you!', 'What can I do for you, sir?', 'Nice to meet you.']
RESPONSE_THANKYOU = ['That is my honor to service you.', 'You are so kind.', 'You are welcome!']
RESPONSE_GOODBYE = ['See you!', 'See you next time!', 'I will always be here.', '88']
RESPONSE_HELP = ['I am a robot created by JACKSON WOO, and maybe he is a little busy, so I am here for you now!',
                 'I can help you find out the latest information about the stock market, such as news, price!']
RESPONSE_CHOOSE = ['Do you like it?', 'Do you interest it?', 'Is that interesting?', 'How about this?', 'This one is better.']
RESPONSE_NOTHING = ["I have heard you, but I can't understand what you said.", "Sorry, I did not get your point ...",
                    'Sorry, I only can say some jokes or get some news for you ...']
RESPONSE_FINISH_JOKE = ['Jackson Woo must be so happy to see your smile!',
                        'You such a gentle in your smile on your face and this can light of the whole world!',
                        "Your smiling is truly sweet, it must be the reason for you are one of Jackson's friend!"]

class Robot:
    
    def __init__(self, conn, interpreter):
        self._conn = conn
        self._interpreter = interpreter

    def session(self):
        '''The robot will do a entire operation in a session.
        '''
        
        intent = self.listen()
        if intent['intent'] == 'greet':
            self.response(choice(RESPONSE_GREET))

        elif intent['intent'] == 'thankyou':
            self.response(choice(RESPONSE_THANKYOU))
            return False

        elif intent['intent'] == 'goodbye':
            self.response(choice(RESPONSE_GOODBYE))
            return False

        elif intent['intent'] == 'search_stock':
            stock, subject = intent.get('stock', None), intent.get('subject', None)
            if stock and subject:
                self.response('I am searching for %s, please wait...' % stock)
            elif stock and not subject:
                subject = self.ask('Which information you want to know about %s, price, news or others?' % stock.upper(), False)
            elif not stock and subject:
                stock = self.ask("Do you want to know which company's %s" % subject, False)
            else:
                stock = self.ask("Sorry, I didn't hear clear, which company you want to know about?", False)
                subject = self.ask('And, what you want to know about %s, news, price or volume?' % stock, False)
            if subject in ('news', 'new', 'info', 'information', 'Journalism'):
                self.do_news(news=None, i=0, key=stock)
            else:
                self.do_stock(stock, subject)

        elif intent['intent'] == 'search_news':
            key = intent.get('key', None)
            while not key:
                key = self.ask("Sorry, please repeat the keyword of the news.", False)
            self.do_news(news=None, i=0, key=key)
            
        elif intent['intent'] == 'search_market':
            self.do_market(intent.get('country', None))
            
        elif intent['intent'] in ('search_joke', 'mood_deny', 'mood_unhappy'):
            self.do_jokes()
            
        elif intent['intent'] == 'help':
           self.response(choice(RESPONSE_HELP))
           
        else:
            self.response(choice(RESPONSE_NOTHING))
            
        return True
            
    def listen(self, parse=True):
        '''Get the information from the client and parse the result
        '''
        MSG = str(self._conn.recv(1024).strip())
        print('Say: %s' % MSG)

        if not parse:
            return MSG

        parse = self._interpreter.parse(MSG)
        obj = {'intent':parse['intent']['name']}
        if obj['intent'] == 'search_stock':
            for ent in parse['entities']:
                if ent.get('entity') == 'stock':
                    obj['stock'] = ent['value']
                elif ent.get('entity') == 'subject':
                    obj['subject'] = ent['value']
                    
        elif obj['intent'] == 'search_news':
            for ent in parse['entities']:
                if ent.get('entity') == 'key':
                    obj['key'] = ent['value']
                    
        elif obj['intent'] == 'search_market':
            for ent in parse['entities']:
                if ent.get('entity') == 'country':
                    obj['country'] = ent['value']
        print(obj['intent'])
        return obj

    def response(self, msg):
        '''Format the message to response
        '''
        if isinstance(msg, list):
            msg = '\n'.join([every for every in msg if every])
        #msg = msg.encode('utf-8')
        print(msg)
        self._conn.sendall(msg + '\n')

    def ask(self, msg, parse=True):
        '''Get more information from the client in one session.
        '''
        self.response(msg)
        self.response('INPUT')
        return self.listen(parse)
    
    def do_market(self, market):
        if market is None:
            market = self.ask('Which market do you prefer, US or China?', False).upper()
            self.do_market(market)
        elif market in ('US', 'U.S', 'U.S.', 'U.S.A', 'AMERICAN', 'UNITED STATES', 'THE UNITED STATES'):
            _nas = self.get_stock('nasdaq')
            _sp = self.get_stock('biaopu')
            _djz = self.get_stock('djz')
            self.response('NASDAQ: %s | S&P 500: %s | Dow Jones: %s' % (_nas, _sp, _djz))
        elif market in ('CHINA', 'CHINESE', 'CHIAN'):
            _shanghai = self.get_stock('shanghai')
            _shenzheng = self.get_stock('shenzheng')
            self.response('Shanghai Composite Index: %s  |  Shenzhen Stock Index: %s' % (_shanghai, _shenzheng))
        else:
            self.response('Sorry, we can not support %s market now.' % market)
            
    def do_stock(self, stock, subject):
        if subject.lower() == 'price':
            intent = self.ask('Do you mean the current price?')['intent']
            if intent in ('mood_deny', 'mood_unhappy'):
                subject = self.ask('So your mean is open, high or low?', False)
            elif intent in ('mood_affirm', 'mood_great'):
                subject = 'current'
            self.do_stock(stock, subject)

        elif subject.lower().endswith('price'):
            self.do_stock(stock, subject[:-5].strip())

        elif subject in ('open', 'current', 'high', 'low'):
            stock_ = self.get_stock(stock)
            if stock_ is None:
                self.response('Failed to get the %s price with unclear reasons.' % subject)
            else:
                self.response('The %s price of %s is $%s per share.' % (subject, stock, stock_[subject]))
        
        elif subject == 'volume':
            stock_ = self.get_stock(stock)
            if stock_ is None:
                self.response('Failed to get the %s price with unclear reasons.' % subject)
            else:
                self.response('The volume of %s is %s.' % (stock, stock_['volume']))
    
        else:
            self.response("I didn't hear clearly, please ask me again.")

    def do_news(self, news=None, i=0, key=None):
        if not news:
            news = self.get_news(key)
            
        self.response(news[i].Title)

        intent = self.ask(choice(RESPONSE_CHOOSE))['intent']
        if intent in ('mood_deny', 'mood_unhappy'):
            self.do_news(news, i+1)
        if intent in ('mood_affirm', 'mood_great'):
            self.response("News' link is %s" % news[i].Link)
        else:
            self.response('Maybe we can change another keyword?')

    def do_jokes(self, jokes=None):
        if not jokes:
            jokes = self.get_jokes()

        self.response(jokes.pop(0))
        intent = self.ask(choice(RESPONSE_CHOOSE))['intent']
        if intent in ('mood_deny', 'mood_unhappy'):
            self.do_jokes(jokes)
        if intent in ('mood_affirm', 'mood_great'):
            self.response(choice(RESPONSE_FINISH_JOKE))
        else:
            self.response('What else I can help you?')

    def get_jokes(self):
        text = get(JOKE_ADDR).text
        soup = BeautifulSoup(text, 'html.parser')
        jokes = soup.findAll(attrs={'class': 'contentHerf'})
        return [joke.span.text for joke in jokes]

    def get_news(self, subject):
        text = get(NEWS_ADDR % subject).text
        soup = BeautifulSoup(text, 'html.parser')
        infos = soup.findAll(attrs={'class': 'r-info r-info2'})
        return [NEWS_FORMAT(subject, info.a.string, info.a['href']) for info in infos if info.a.string is not None]

            
    def get_stock(self, stock):
        stock_ID, market = self.get_stock_info(stock)
        try:
            data = get(STOCK_ADDR % (market, stock_ID)).text.encode('cp936').split('"')[1].split(',')
        except:
            return None
        try:
            if market in ('sh', 'sz'):
                data = {'Name': data[0],
                        'open': data[1],
                        'high': data[4],
                        'low': data[5],
                        'current': data[3],
                        'volume': data[8]}
            elif market == 'gb_':
                data = {'Name': data[0],
                        'open': data[5],
                        'high': data[6],
                        'low': data[7],
                        'current': data[1],
                        'volume': data[10]}
            elif market == 'hk':
                data = {'Name': data[1],
                        'open': data[2],
                        'high': data[4],
                        'low': data[5],
                        'current': data[6],
                        'volume': data[12]}
            elif market == 'int_':
                return data[1]
            return data
        except:
            return None

    def get_stock_info(self, stock):
        with sql.connect('data/STOCK_NUM.db') as conn:
            cur = conn.cursor()
            cur.execute('SELECT * FROM stocks WHERE Name="%s"' % stock.lower())
            data = cur.fetchone()

        if data is not None:
            return data[0][1:].lower(), data[2]
        self.response("Sorry, I didn't have the number for this stock.")
        return '', ''
