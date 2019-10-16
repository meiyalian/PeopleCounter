# PeopleCounter


A program that reads in a video and counts the number of times people walking up/down across a self-defined line.
This program is for upskilling purpose, it contains two python files. Both files use the same logic to implement the counting function and use Tkinter to implement the GUI.


### peopleCounterSingleLine.py

In this file, the program takes a video and counts the number of times people walking up/down across a single line.The GUI allows you to:

*Draw the line

*Define the margin of errors (the max. number of pixies allows between a person and the line when the program determines that the person is acrossing the line) -- default value is 15 px.

*Start/Pause/Resume the video

*Displaying the current distance between the person and the line, as well as the prediction of that person's direction (up/down). This function is only applicable to videos that only contain one person. 

![GUI](https://i.imgur.com/U3g7yc8.png)


### peopleCounterWithGUI.py

In this file, you need to draw two lines to enable the program counting people going up/down across the lines. 


![GUI](https://i.imgur.com/VsFg74d.png)
