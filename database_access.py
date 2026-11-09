import sqlite3

conn=sqlite3.connect("easystay.db")
cursor=conn.cursor()
def table_creation():
    cursor.execute("""
                create table if not exists guests
                (guest_name varchar(90) not null,
                mobile_number text primary key check(mobile_number glob '[6-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]'),
                email varchar(90) not null)
                """)
    conn.commit()
    cursor.execute("""
                create table if not exists rooms(room_no int primary key,
                room_type varchar(90) not null check(room_type in ("Standard","Deluxe","Suite")),
                floor int not null)
                """)
    conn.commit()
    cursor.execute("""
                create table if not exists bookings(
                    booking_id integer primary key autoincrement,
                    mobile_number text not null references guests(mobile_number),
                    room_no int not null references rooms(room_no),
                    no_of_guests int check(no_of_guests between 1 and 4),
                    status varchar(90) check(status in ("CHECKED_IN","CHECKED_OUT","CONFIRMED","CANCELLED")),
                    room_charges int not null,
                    extra_guest_charges int not null,
                    long_stay_discount int not null,
                    loyalty_discount int not null,
                    gst int not null default 0,
                    total_amount int null,
                    refund_amount int not null,
                    check_in text not null,
                    check_out text not null,
                    check(check_in<check_out)
                )
                """)
    conn.commit()

def insert_rooms(room_no,room_type,floor):
    query="""
    insert or ignore into rooms(room_no,room_type,floor) values(?,?,?)
    """
    cursor.execute("select 1 from rooms where room_no=?",(room_no,))
    if cursor.fetchone():
        # print("room already exists")
        return 
    else:
        try:
            cursor.execute(query,(room_no,room_type,floor))
            conn.commit()
        except Exception:
            print("some error occured in db cannot insert into db")



def check_overlapping(type,in_,out):
    query=""" select r.room_no 
    from rooms r
    where r.room_type=? and not exists(
    select 1 from bookings b
    where 
    b.room_no=r.room_no and
    b.check_in<? and b.check_out>? 
    and b.status in("CHECKED_IN","CONFIRMED"))
    """
    cursor.execute(query,(type,out,in_))
    data=cursor.fetchall()
    for row in data:
        print(row)
    if len(data)==0:
        print("these are the alternative rooms for different room type")
        alternate_query="""
        select r.room_no,r.room_type
        from rooms r
        where r.room_type != ?
        and not exists(
        select 1
        from bookings b
        where b.room_no = r.room_no
        and b.check_in < ?
        and b.check_out > ?
        and b.status in("CHECKED_IN","CONFIRMED"))
        """
        cursor.execute(alternate_query,(type,out,in_))
        data=cursor.fetchall()
        for row in data:
            print(row)

def get_guest(mobile):
    cursor.execute("""
    select guest_name,mobile_number,email
    from guests
    where mobile_number=?
    """,(mobile,))
    return cursor.fetchone()

def insert_guest(name,mobile,email):
    cursor.execute("""
    insert into guests(guest_name,mobile_number,email)
    values(?,?,?)
    """,(name,mobile,email))
    conn.commit()
    

def get_available_rooms(type,in_,out):
    query=""" select r.room_no,r.room_type
    from rooms r
    where r.room_type=? and not exists(
    select 1 from bookings b
    where 
    b.room_no=r.room_no and
    b.check_in<? and b.check_out>? 
    and b.status in("CHECKED_IN","CONFIRMED"))
    """
    cursor.execute(query,(type,out,in_))
    data=cursor.fetchall()
    if len(data)==0:
        print("these are the alternative rooms for different room type")
        alternate_query="""
        select r.room_no,r.room_type
        from rooms r
        where r.room_type != ?
        and not exists(
        select 1
        from bookings b
        where b.room_no = r.room_no
        and b.check_in < ?
        and b.check_out > ?
        and b.status in("CHECKED_IN","CONFIRMED"))
        """
        cursor.execute(alternate_query,(type,out,in_))
        data=cursor.fetchall()
        return data
    else:
        return data

def get_completed_stays(mobile):
    cursor.execute("""
    select count(*)
    from bookings
    where mobile_number=?
    and status="CHECKED_OUT"
    """,(mobile,))
    return cursor.fetchone()[0]


def insert_booking(mobile,room_no,guests,room_charges,extra_guest_charges,long_discount,loyalty_discount,gst,total,check_in,check_out):
    cursor.execute("""
    insert into bookings(
        mobile_number,room_no,no_of_guests,status,
        room_charges,extra_guest_charges,
        long_stay_discount,loyalty_discount,
        gst,total_amount,refund_amount,
        check_in,check_out
    )
    values(?,?,?,"CONFIRMED",?,?,?,?,?,?,0,?,?)
    """,(mobile,room_no,guests,room_charges,extra_guest_charges,long_discount,loyalty_discount,gst,total,check_in,check_out))
    booking_id=cursor.lastrowid
    conn.commit()
    return booking_id
    
def booking_id(booking_id):
    cursor.execute("""
    select booking_id,room_no,status,check_in,check_out
    from bookings
    where booking_id=?
    """,(booking_id,))
    return cursor.fetchone()

def checkin(booking_id):
    cursor.execute("""
    update bookings
    set status="CHECKED_IN"
    where booking_id=? and status="CONFIRMED"
    """,(booking_id,))
    conn.commit()
    return cursor.rowcount


def checkout(booking_id):
    cursor.execute("""
    update bookings
    set status="CHECKED_OUT"
    where booking_id=? and status="CHECKED_IN"
    """,(booking_id,))
    conn.commit()
    return cursor.rowcount


def invoice(booking_id):
    cursor.execute("""
    select b.booking_id,g.guest_name,g.mobile_number,g.email,
           r.room_no,r.room_type,b.no_of_guests,
           b.check_in,b.check_out,
           b.room_charges,b.extra_guest_charges,
           b.long_stay_discount,b.loyalty_discount,
           b.gst,b.total_amount
    from bookings b
    join guests g on b.mobile_number=g.mobile_number
    join rooms r on b.room_no=r.room_no
    where b.booking_id=?
    """,(booking_id,))
    return cursor.fetchone()

def details_cancel_booking(booking_id):
    cursor.execute("""
    select booking_id,status,check_in,total_amount
    from bookings
    where booking_id=?
    """,(booking_id,))
    return cursor.fetchone()

def cancel(booking_id,refund):
    cursor.execute("""
    update bookings
    set status="CANCELLED",refund_amount=?
    where booking_id=? and status="CONFIRMED"
    """,(refund,booking_id))
    conn.commit()
    return cursor.rowcount

def booking_details(booking_id):
    cursor.execute("""
    select b.booking_id,g.guest_name,g.mobile_number,g.email,
           r.room_no,r.room_type,b.no_of_guests,
           b.check_in,b.check_out,b.status,
           b.room_charges,b.extra_guest_charges,
           b.long_stay_discount,b.loyalty_discount,
           b.gst,b.total_amount,b.refund_amount
    from bookings b
    join guests g on b.mobile_number=g.mobile_number
    join rooms r on b.room_no=r.room_no
    where b.booking_id=?
    """,(booking_id,))
    return cursor.fetchone()

def guest_history(mobile):
    cursor.execute("""
    select b.booking_id,r.room_no,r.room_type,
           b.check_in,b.check_out,b.status,b.total_amount
    from bookings b
    join rooms r on b.room_no=r.room_no
    where b.mobile_number=?
    order by b.check_in desc
    """,(mobile,))
    return cursor.fetchall()

def report_by_occupancy(start_date,end_date):
    cursor.execute("""
    select r.room_type,count(distinct b.room_no)
    from bookings b
    join rooms r on b.room_no=r.room_no
    where b.check_in<? and b.check_out>?
    and b.status in ("CONFIRMED","CHECKED_IN","CHECKED_OUT")
    group by r.room_type
    """,(end_date,start_date))
    return cursor.fetchall()

def report_of_revenue():
    cursor.execute("""
    select r.room_type,sum(b.total_amount-b.refund_amount)
    from bookings b
    join rooms r on b.room_no=r.room_no
    where b.status in ("CHECKED_OUT","CANCELLED")
    group by r.room_type
    """)
    return cursor.fetchall()

def booking_total():
    cursor.execute("""
    select b.booking_id,g.guest_name,g.mobile_number,g.email,
           r.room_no,r.room_type,b.no_of_guests,
           b.check_in,b.check_out,b.status,
           b.room_charges,b.extra_guest_charges,
           b.long_stay_discount,b.loyalty_discount,
           b.gst,b.total_amount,b.refund_amount
    from bookings b
    join guests g on b.mobile_number=g.mobile_number
    join rooms r on b.room_no=r.room_no
    """)
    return cursor.fetchall()