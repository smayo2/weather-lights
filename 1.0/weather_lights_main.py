
import RPi.GPIO as GPIO
import os, requests, json, threading
from time import sleep
from http.server import BaseHTTPRequestHandler, HTTPServer
#from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
#Ref: https://github.com/e-tinkers/simple_httpserver


host_name = '192.168.43.77'  # Change this to your Raspberry Pi IP address
host_port = 8000
OWM_Key = 'YOUR_OWN_KEY' #Key from api.openweathermap.org
location_name = 'London,UK'
unit_type = 'metric' #change to 'imperial' if appropriate
weather_update_interval = 120 #interval in seconds to update the weather data
#weather threshold values (metric)
get_reading=True


class MyServer(BaseHTTPRequestHandler):
    """ A special implementation of BaseHTTPRequestHander for reading data from
        and control GPIO of a Raspberry Pi
    """
    #set default threshold values
    min_temp = 10
    max_temp = 15
    current_temp_str = '9999 oC'    
    red_led = 18
    blue_led = 24

    def lighter2():
     while (get_reading):
        #read temperature data from API
        print ('Thread 1: Reading weather data')
        weather_response = requests.get ('http://api.openweathermap.org/data/2.5/weather?q='+location_name+'&units='+unit_type+'&appid='+OWM_Key)
        current_weather = json.loads(weather_response.text)
        current_temp = current_weather['main']['temp']
        print(current_temp, 'oC')
        MyServer.current_temp_str = str(current_temp)+' oC'

        # GPIO setup
        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)
        GPIO.setup(MyServer.red_led, GPIO.OUT)
        GPIO.setup(MyServer.blue_led, GPIO.OUT)

        this_min_temp = MyServer.min_temp
        this_max_temp = MyServer.max_temp
        print ('Min. temperature threshold is: ', this_min_temp)
        print ('Max. temperature threshold is: ', this_max_temp)       
        print("Current Temperature is: ", current_temp)

        #indicate with LEDs if minimum or maximum thresholds exceed             
        if current_temp <= int(this_min_temp):
            GPIO.output(MyServer.blue_led, GPIO.HIGH)
            GPIO.output(MyServer.red_led, GPIO.LOW)
            print("Temperature is too low at: ", current_temp)
        elif current_temp >= int(this_max_temp):
            GPIO.output(MyServer.red_led, GPIO.HIGH)
            GPIO.output(MyServer.blue_led, GPIO.LOW)            
            print("Temperature is too high at: ", current_temp)
        else:                  
            print("Temperature is fine!")
            GPIO.output(MyServer.red_led, GPIO.LOW)
            GPIO.output(MyServer.blue_led, GPIO.LOW)
                                         
        sleep(weather_update_interval)

    
    def do_HEAD(self):
        """ do_HEAD() can be tested use curl command
            'curl -I http://server-ip-address:port'
        """
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

    def _redirect(self, path):
        self.send_response(303)
        self.send_header('Content-type', 'text/html')
        self.send_header('Location', path)
        self.end_headers()
        
     
    def do_GET(self):
        """ do_GET() can be tested using curl command
            'curl http://server-ip-address:port'
        """
        html = '''
           <html>
           <body style="margin:50px;background-color:yellow; font-size:2em">
           <h1>Welcome to my Raspberry Pi</h1>
           <hr>
           <p>Current temperature is {}</p>           
           <form action="/" method="POST">
               Turn LED :
               <input type="submit" name="submit" value="On">
               <input type="submit" name="submit" value="Off">
               <br><br><br><hr>

           <p> *Threshold settings* </p>
               Min. temperature: 
               <input type="text" name="min_temp_input"><br><br>
               Max. temperature: 
               <input type="text" name="max_temp_input"><br><br>
               <input type="submit" value="Submit">
           </form>
           <hr>
           <br><br<br><br><br>
           </body>
           </html>
        '''        
      
        self.do_HEAD()
        self.wfile.write(html.format(MyServer.current_temp_str).encode("utf-8"))
        #self._redirect('/')  # Redirect back to the root url
    
   
    
    def do_POST(self):
        """ do_POST() can be tested using curl command
            'curl -d "submit=On" http://server-ip-address:port'
        """
        #extract data input (settings) sent by user
        content_length = int(self.headers['Content-Length'])  # Get the size of data
        post_data = self.rfile.read(content_length).decode("utf-8")  # Get the data
        post_data_val = post_data.split("=")  # Only keep the value
        post_data = post_data_val[1].split("&")[0]  # Only keep the value after &
        this_max_temp_str = post_data_val[2].split("&")[0]
               
        if post_data == 'On':
            GPIO.output(MyServer.red_led, GPIO.HIGH)
        elif post_data == 'Off':
            GPIO.output(MyServer.red_led, GPIO.LOW)
        else:
            this_min_temp_str = post_data
            MyServer.min_temp = this_min_temp_str
            MyServer.max_temp = this_max_temp_str
        self._redirect('/')  # Redirect back to the root url
        

if __name__ == '__main__':
        #thread that reads weather info
        
        http_server = HTTPServer((host_name, host_port), MyServer)        
        print("\n Server Starts - %s:%s" % (host_name, host_port))
        weather_thread = threading.Thread(target= MyServer.lighter2).start()
       
        try:
            http_server.serve_forever()
        except KeyboardInterrupt:
            get_reading = False
            http_server.server_close()
            #turn off LEDs and clean up GPIO
            GPIO.cleanup()
