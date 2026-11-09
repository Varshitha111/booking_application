from abc import ABC,abstractmethod
import sqlite3
from datetime import datetime,timedelta
import csv
from exceptions import invalid_room,duplicate_room_num 
import database_access
import logging

class Room(ABC):
    def __init__(self,room_no):
        self.room_no=room_no
    @abstractmethod
    def get_rate(self):
        pass
    @abstractmethod
    def get_capacity(self):
        pass

class StandardRoom(Room):
    def get_rate(self):
        return 2500
    def get_capacity(self):
        return 2

class DeluxeRoom(Room):
    def get_rate(self):
        return 4000
    def get_capacity(self):
        return 3

class SuiteRoom(Room):
    def get_rate(self):
        return 7500
    def get_capacity(self):
        return 4    
    
def room_verification():
    with open("rooms.csv", "r") as file:
        lst = []
        reader=csv.reader(file)
        next(reader, None)
        row_count=0
        for row in reader:
            row_count+=1
            try:
                if len(row) != 3:
                    raise invalid_room("each row must contain exactly 3 columns")
                roomno=row[0].strip()
                roomtype=row[1].strip()
                floor=row[2].strip()
                if roomno=="" or roomtype=="" or floor=="":
                    raise invalid_room("room details cannot be empty")
                try:
                    roomno=int(roomno)
                    if roomno<=0:
                        raise invalid_room("room number must be positive")
                except ValueError:
                    raise invalid_room("room number must be an integer")
                if roomtype not in ("Standard", "Deluxe", "Suite"):
                    raise invalid_room("invalid room type")
                try:
                    floor=int(floor)
                    if floor<0:
                        raise invalid_room("floor cannot be negative")
                except ValueError:
                    raise invalid_room("floor must be an integer")
                if roomno in lst:
                    raise duplicate_room_num("the room number already exists")
                lst.append(roomno)
                database_access.insert_rooms(roomno,roomtype,floor)
            except invalid_room as e:
                with open("app.log","a") as file:
                    file.write(f"invalid row {reader.line_num}: {row}-{e}\n")
            except duplicate_room_num as e:
                with open("app.log","a") as file:
                    file.write(f"invalid row {reader.line_num}: {row}-{e}\n")
        if row_count==0:
            print("no room data")

def room_search_availability():
    try:
        total_nights=0
        check_in=input("enter the check-in date (DD-MM-YYYY)")
        check_out=input("enter the check-out date (DD-MM-YYYY)")
        room_type=input("enter the room type")
        no_of_guests=int(input("enter the number of guests"))
        check_in=datetime.strptime(check_in,"%d-%m-%Y").date()
        check_out=datetime.strptime(check_out,"%d-%m-%Y").date()
        today=datetime.now().date()
        if today<=check_in<=today+timedelta(days=180):
            total_nights=(check_out-check_in).days
            if 1<=total_nights<=30:
                if room_type not in ("Standard","Deluxe","Suite"):
                    print("invalid room type")
                elif no_of_guests<1 or no_of_guests>4:
                    print("guests must be between 1 and 4")
                elif no_of_guests>2 and room_type=="Standard":
                    print("standard room should contain only 2 people")
                elif no_of_guests>3 and room_type=="Deluxe":
                    print("Deluxe room should contain maximum of 3 people")
                else:
                    database_access.check_overlapping(room_type,check_in.isoformat(),check_out.isoformat())
            else:
                print("Stays are permitted for 1-30 days only")
        else:
            print("Check-in must be between today and the next 180 days")
    except ValueError:
        print("Invalid date or guest count")
        
def create_booking():
    try:
        while True:
            guest_name=input("enter guest name").strip()
            if guest_name!="":
                break
            print("guest name cannot be empty")
        while True:
            mobile=input("enter mobile number:").strip()
            guest=database_access.get_guest(mobile)
            if guest:
                print("guest already registered")
                break
            email=input("enter email").strip()
            if email=="":
                print("email cannot be empty")
                continue
            try:
                database_access.insert_guest(guest_name,mobile,email)
                break
            except Exception:
                print("invalid mobile number or guest details, try again")
        while True:
            try:
                check_in=input("enter check-in date(DD-MM-YYYY):")
                check_in_date=datetime.strptime(check_in,"%d-%m-%Y").date()
                today=datetime.now().date()
                if today<=check_in_date<=today+timedelta(days=180):
                    break
                print("check-in must be between today and the next 180 days")
            except ValueError:
                print("invalid date try again")
        while True:
            try:
                check_out=input("enter check-out date (DD-MM-YYYY): ")
                check_out_date=datetime.strptime(check_out,"%d-%m-%Y").date()
                nights=(check_out_date-check_in_date).days
                if 1<=nights<=30:
                    break
                print("stay must be between 1 and 30 nights")
            except ValueError:
                print("invalid date try again")
        while True:
            room_type=input("enter room type")
            if room_type=="Standard":
                room=StandardRoom(0)
                break
            elif room_type=="Deluxe":
                room=DeluxeRoom(0)
                break
            elif room_type=="Suite":
                room=SuiteRoom(0)
                break
            print("invalid room try again")
        while True:
            try:
                no_of_guests=int(input("enter number of guests"))
                if 1<=no_of_guests<=room.get_capacity():
                    break
                print("invalid number of guests for this room")
            except ValueError:
                print("please enter a number")
        breakfast="n"
        if room_type=="Standard":
            while True:
                breakfast=input("do you want breakfast? (y/n)").lower()
                if breakfast in ("y","n"):
                    break
                print("please enter y or n")
        # check room availability
        available_rooms=database_access.get_available_rooms(room_type,check_in_date.isoformat(),check_out_date.isoformat())
        if len(available_rooms)==0:
            print("no rooms available for the selected dates")
            return
        alternative_rooms=[]
        for available_room in available_rooms:
            if available_room[1]=="Standard" and no_of_guests<=2:
                alternative_rooms.append(available_room)
            elif available_room[1]=="Deluxe" and no_of_guests<=3:
                alternative_rooms.append(available_room)
            elif available_room[1]=="Suite" and no_of_guests<=4:
                alternative_rooms.append(available_room)
        if available_rooms[0][1]!=room_type:
            print("available alternative rooms:")
            if len(alternative_rooms)==0:
                print("no suitable alternative rooms available")
            else:
                for available_room in alternative_rooms:
                    print(available_room)
            return
        # allocate the lowest numbered room
        room_no=available_rooms[0][0]
        room.room_no=room_no
        print("allocated room number:",room_no)

        # calculate room charges
        rate=room.get_rate()
        room_charges=0
        for i in range(nights):
            current_date=check_in_date+timedelta(days=i)
            if current_date.weekday() in (4,5):
                room_charges=room_charges+rate*1.20
            else:
                room_charges=room_charges+rate
        room_charges=round(room_charges)
        # calculate extra guest charges
        extra_guest_charges=0
        if room_type in ("Deluxe","Suite") and no_of_guests>2:
            extra_guest_charges=(no_of_guests-2)*800*nights
        # calculate breakfast charges
        breakfast_charges=0
        if breakfast=="y":
            breakfast_charges=350*no_of_guests*nights
        room_charges=room_charges+breakfast_charges
        # calculate long stay discount
        long_discount=0
        if nights>=7:
            long_discount=round((room_charges-breakfast_charges)*0.10)
        # calculate loyalty discount
        completed_stays=database_access.get_completed_stays(mobile)
        loyalty_discount=0
        if completed_stays>=3:
            loyalty_discount=round((room_charges-breakfast_charges-long_discount)*0.05)
        # calculate gst
        taxable_amount=room_charges+extra_guest_charges-long_discount-loyalty_discount
        if rate<=7500:
            gst=round(taxable_amount*0.12)
        else:
            gst=round(taxable_amount*0.18)
        total=taxable_amount+gst
        print("room charges",room_charges)
        print("extra guest charges",extra_guest_charges)
        print("long stay discount",long_discount)
        print("loyalty discount",loyalty_discount)
        print("gst",gst)
        print("total amount",total)
        booking_id=database_access.insert_booking(
            mobile,room_no,no_of_guests,
            room_charges,extra_guest_charges,
            long_discount,loyalty_discount,
            gst,total,
            check_in_date.isoformat(),
            check_out_date.isoformat()
        )
        
        print("your booking id is:",booking_id)
    except Exception as e:
        print("booking failed:",e)
        return
    
def check_in():
    try:
        booking_id=int(input("enter booking id"))
        booking=database_access.booking_id(booking_id)
        if booking is None:
            print("booking not found")
        elif booking[2]=="CONFIRMED":
            result=database_access.checkin(booking_id)
            if result:
                print("checked ins")
        else:
            print("booking cannot be checked in because current status",booking[2])

    except ValueError:
        print("enter value in int")
        
def check_out():
    try:
        booking_id=int(input("enter booking id"))
        booking=database_access.booking_id(booking_id)

        if booking is None:
            print("booking not found")
        elif booking[2]=="CHECKED_IN":
            result=database_access.checkout(booking_id)
            if result:
                print("checked out")
                invoice_generator(booking_id)
        else:
            print("booking cannot be checked out because current status",booking[2])
    except ValueError:
        print("enter numbers only")
def invoice_generator(booking_id):
    data=database_access.invoice(booking_id)
    print("invoice")
    print(f"booking id{data[0]}")
    print(f"guest name{data[1]}")
    print(f"mobile{data[2]}")
    print(f"email{data[3]}")
    print(f"room number{data[4]}")
    print(f"room type{data[5]}")
    print(f"number of guests{data[6]}")
    print(f"check-in{data[7]}")
    print(f"check-out{data[8]}")
    print(f"room charges{data[9]}")
    print(f"extra guest charges{data[10]}")
    print(f"long stay discount{data[11]}")
    print(f"loyalty discount{data[12]}")
    print(f"gst: {data[13]}")
    print(f"total amount: {data[14]}")
    
def cancel():
    try:
        booking_id=int(input("enter booking id: "))
        booking=database_access.details_cancel_booking(booking_id)
        if booking is None:
            print("booking not found")
            return
        if booking[1]!="CONFIRMED":
            print("cancellation not possible")
            return
        check_in=datetime.strptime(booking[2],"%Y-%m-%d").date()
        today=datetime.now().date()
        days=(check_in-today).days
        if days>=7:
            refund=booking[3]
        elif days>=2:
            refund=round(booking[3]*0.50)
        else:
            refund=0
        database_access.cancel(booking_id,refund)
        print("refund amount",refund)
    except ValueError:
        print("please enter a valid booking id")
    except Exception as e:
        print("cancellation failed:",e)
        
def view_booking_details():
    try:
        booking_id=int(input("enter booking id "))
        data=database_access.booking_details(booking_id)
        if data is None:
            print("booking not found")
            return
        print("booking id",data[0])
        print("guest name",data[1])
        print("mobile",data[2])
        print("email",data[3])
        print("room number",data[4])
        print("room type",data[5])
        print("guests",data[6])
        print("check-in",data[7])
        print("check-out",data[8])
        print("status",data[9])
        print("room charges",data[10])
        print("extra guest charges",data[11])
        print("long stay discount",data[12])
        print("loyalty discount",data[13])
        print("gst",data[14])
        print("total amount",data[15])
        print("refund amount",data[16])
    except ValueError:
        print("enter a valid booking id")
        
def guest_history_by_mobile():
    mobile=input("enter mobile number").strip()
    data=database_access.guest_history(mobile)
    if len(data)==0:
        print("no bookings")
        return
    for booking in data:
        print("booking id",booking[0])
        print("room number",booking[1])
        print("room type",booking[2])
        print("check-in",booking[3])
        print("check-out",booking[4])
        print("status",booking[5])
        print("total amount",booking[6])
        
def occupancy_report():
    try:
        start=input("enter start date (DD-MM-YYYY)")
        start_date=datetime.strptime(start,"%d-%m-%Y").date()
        end=input("enter end date (DD-MM-YYYY)")
        end_date=datetime.strptime(end,"%d-%m-%Y").date()
        if start_date>=end_date:
            print("end date must be after start date")
            return
        data=database_access.report_by_occupancy(
            end_date.isoformat(),start_date.isoformat()
        )
        if len(data)==0:
            print("no bookings on this occupancy")
            return
        for row in data:
            print("room type",row[0])
            print("occupied rooms",row[1])
    except ValueError:
        print("invalid date format")
        
        
def revenue_report():
    data=database_access.report_of_revenue()
    if len(data)==0:
        print("no revenue records found")
        return
    for row in data:
        print("room type",row[0])
        print("revenue",row[1])

def export_csv():
    data=database_access.booking_total()
    if not data:
        print("no bookings available")
        return
    with open("bookings.csv","w") as file:
        writer=csv.writer(file)
        writer.writerow(["booking_id","guest_name","mobile","email","room_no","room_type","guests","check_in","check_out","status","room_charges","extra_guest_charges","long_stay_discount","loyalty_discount","gst","total_amount","refund_amount"])
        for row in data:
            writer.writerow(row)