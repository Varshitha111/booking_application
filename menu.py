import database_access
import models


database_access.table_creation()
def menu_method():
    while True:
        try:
            choice=int(input("choose one option\n1. Search room availability \n2. Create booking \n3. Check in \n4. Check out (generate invoice) \n5. Cancel booking \n6. View booking details \n7. Guest stay history (by mobile number) \n8. Occupancy report (for a date range) \n9. Revenue report (by room type) \n10. Export all bookings to CSV \n11. Exit "))
            match choice:
                case 1:
                    models.room_search_availability()
                case 2:
                    models.create_booking()
                case 3:
                    models.check_in()
                case 4:
                    models.check_out()
                case 5:
                    models.cancel()
                case 6:
                    models.view_booking_details()
                case 7:
                    models.guest_history_by_mobile()
                case 8:
                    models.occupancy_report()
                case 9:
                    models.revenue_report()
                case 10:
                    models.export_csv()
                case 11:
                    break
                case _:
                    print("Enter valid choice ")
        except ValueError:
            print("enter the integers only")    