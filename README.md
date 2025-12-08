# printer spooler problem

## About
This project is about the **printer spooler** problem and its solution with printer model Xprinter XP58-IIN USB
### what is a printer spooler problem?
Printer spooler problem is a classic synchronization issue, where multiple processes attempt to access a shared resource, \
in this case, a printer.\
<img width="451" height="374" alt="image describing an printer spooler problem" src="https://github.com/user-attachments/assets/e54fad39-48a0-4d9d-8799-bda634ff428f" />

## Solution
My solution is using a doubly LinkedList wtih priority queue. The LinkedList(TaskList) is secured by threading.Lock to have it thread secure. The priority queue is used because some documents needed to be printed sooner than other.

## Operation system
This project is only for Windows.

## Set up

### Step 1
Download the newest release v2.0.0. You need to have the printer connected in the same device thru USB where the server runs. 

### Step 2
When downloaded and the printer is connected now we need to configure printers in Windows settings.  
Go to Control Panel -> Device and Printers -> Add a printer -> Select Add a local printer -> Choose Use an existing port (select Printer USB Printer Port) -> Select the printer driver (choose Generic / Text only) -> Give the printer name (**Xprinter**) <---- the name must be like this or it will not work  
**And thats all**

## How To use
When the server is started you can connect to it with devices on the same network. On the webpage you can upload .pdf files and the printer prints it.





