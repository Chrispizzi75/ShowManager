## LightShowPi show manager


**Lightshowpi show manager works with Python 3 and above.**


** Requirements:**

- LightshowPi: but if you are here I suppose you have already installed it :-).


- REMI: Python REMote Interface library. 
	https://github.com/dddomodossola/remi - 
	pip install git+https://github.com/dddomodossola/remi.git



**Installation:**

there is nothing to install to use LightShowPi show manager. 
The important thing is that you have “Lightshowpi_show_manager.py” file in the same folder where you have /res folder. 
“/res” contain the pictures and the CSS files used by the app.

It's possible lunch the program in a shell:
move to the folder where you downloaded the file:
		example:  cd /home/pi/LightShowPI_show_manager
lunch the application:
		python3 Lightshowpi_show_manager.py

or use your favorite IDE and run your app from there.

This app use REMI as web server, and try to start the app using the address:
127.0.0.1:8081 or “your Raspberry pi address”:8081, example 192.168.0.104:8081
if the port 8081 is already used you can modify it in the app.
This is the line where you can change the address and the port; it's located at the bottom of the program:
start(MyApp, address='', port=8081, start_browser=True, username=None, password=None)
it's possible specify the address='your-raspberry-pi-address' example address='192.168.0.104'
and/or the port you want to use; port='8081' is the default one but you can specify what you have available.

When you have lunched your app, it automatically opens the default browser on the '127.0.0.1:8081' (or what you have changed before) page. If that doesn't happen you can manually open the browser and navigate to '127.0.0.1:8081' page.
In the same way you can connect your smartphone and access to the same page and manage the app with your phone. This is why I've created this app, to be able to control my show from my phone.
One important thing: the smartphone must be connected to the same wi-fi network of your Raspberry pi (the wi-fi connection must be on).

**Version 1.3 released**

App updated to work with the last release of REMI 2020.8.6.
Added scheduler.