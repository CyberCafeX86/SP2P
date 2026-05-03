# SP2P
A simple P2P chat written in Python.

## How to use it
First download the script (there is no necessary external library) and run it:
```
./router.py
```
Or
```
python3 router.py
```
It opens a "global port" (default 50000), this is the port you will indicate to others connect to you or you connect to others.  
To connect on a single peer you know the IP and its global port, only use the command:
```
SP2P > connect_single <target ip> <target global port>
```
You can connect to many peers starting from a single known peer and its global port:
```
SP2P > connect <target ip> <target global port>
```
This command will first ask for known devices from the specified peer, then connect to that peer and to the other peers it provides.

You can check all available commands with "help" command.

## Technical

On this protocol, there is a TCP port who always active (reffered as "global port"), this port has 3 jobs:  
- Receive new connections
- Give peers to another peer connect
- Test connectivity

It is a stateless port (it does not keep the connection open).  

When connecting, the client sends its own global_port; this is used so the peer can share your information with others.  
To connect to a peer, your client must send a number, this number will be your global_port.  
After that, the peer you connect to sends another number: this will be a stateful port where the continuous peer-to-peer connection will take place.  
When discovering new peers from a specific peer (using the connect ```command```), the requester sends its global port in a ```DISCOVER``` message. The contacted peer responds with a list of available peers and their global ports.

> [!WARNING]
> This project is for educational/fun purposes. It includes no cryptography, authentication, or authorization. Running it over the Internet requires port forwarding. Use at your own risk.

> [!NOTE]
> This project was made with no AI.
