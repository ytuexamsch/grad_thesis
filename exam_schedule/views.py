from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
import pandas as pd
import numpy as np
import pulp
import time


# Create your views here.
def home(request):
    return render(request, 'home.html')


def upload(request):
    return render(request, 'upload.html')


########################################################################################################################
# Schedule 1'de hızlı çalışsın diye belirli kısıtlar konuldu.

def schedule(request):
    file = 'media/' + request.POST.get('file_name')

    limit_same_time_2 = request.POST.get('limit_same_time_2')
    limit_same_time_3 = request.POST.get('limit_same_time_3')
    limit_same_time_4 = request.POST.get('limit_same_time_4')
    limit_pespese_2 = request.POST.get('limit_pespese_2')
    limit_pespese_3 = request.POST.get('limit_pespese_3')

    # GÜNLER VE SAATLER
    days_slots = pd.read_excel(file, usecols="AI:AJ", skiprows=14, nrows=10)
    days = days_slots["DAYS"].dropna().values.astype(int)  ##############
    slots = days_slots["TIMEINTERVAL"].dropna().values.astype(int)  #############

    # DERSLER
    courses_and_capacities = pd.read_excel(file, usecols="B:D")
    courses_and_capacities.drop(courses_and_capacities.index[0], inplace=True)
    courses_and_capacities.dropna(inplace=True)
    course = courses_and_capacities["COURSE \nNO"].values  ###############
    course_name_dict = dict(zip(course, courses_and_capacities["ALL COURSES"]))
    course_capacity_dict = dict(zip(course, courses_and_capacities["CAPACITY OF COURSES"].values))  ##############

    # SINIFLAR
    classroom_and_capacities = pd.read_excel(file, usecols="AJ:AL")
    classroom_and_capacities.drop(classroom_and_capacities.index[0], inplace=True)
    classroom_and_capacities.dropna(inplace=True)
    classroom = classroom_and_capacities["CLASSROOMS"].values  ##############
    classroom_capacity_dict = dict(zip(classroom, classroom_and_capacities["Capacity"].values))  ############

    problem = pulp.LpProblem('Exam_Assigment_Problem', pulp.LpMinimize)
    X_assign = pulp.LpVariable.dicts('Assign_with_classroom', (course, classroom, days, slots), lowBound=0, upBound=1,
                                     cat=pulp.LpBinary)
    Z_assign = pulp.LpVariable.dicts('Assign_without_classroom', (course, days, slots), lowBound=0, upBound=1,
                                     cat=pulp.LpBinary)

    # (1) Bir sınıfa bir günde ve bir intervalda birden fazla ders atanmasın
    for j in classroom:
        for d in days:
            for t in slots:
                problem += pulp.lpSum([X_assign[i][j][d][t] for i in course]) <= 1

                # (2) Her bir ders bir güne ve bir saate atanmalı, ders boşta kalmasın kısıtı.
    for i in course:
        problem += pulp.lpSum([Z_assign[i][d][t] for d in days for t in slots]) == 1

        # (14) İki değişkenin bağlantısını aşağıdaki kısıtlarla sağlaycağız.
    for i in course:
        for d in days:
            for t in slots:
                problem += pulp.lpSum([X_assign[i][j][d][t] for j in classroom]) >= Z_assign[i][d][t]

                # (15) İki değişkenin bağlantısını aşağıdaki kısıtlarla sağlaycağız -2.
    for i in course:
        for d in days:
            for t in slots:
                problem += pulp.lpSum([X_assign[i][j][d][t] for j in classroom]) <= 5 * Z_assign[i][d][t]

    problem += pulp.lpSum([X_assign[i][j][d][t] for i in course for j in classroom for d in days for t in slots])

    start = time.time()
    problem.solve()
    end = time.time()
    optimal_check = pulp.LpStatus[problem.status]
    solution_time = round((end - start))

    assign_list = []
    for d in days:
        for t in slots:
            # print('Day:', d, ' Slot:',t )
            for v in problem.variables():
                if v.value() == 1:
                    if "_" + str(d) + "_" + str(t) in v.name and 'with_' in v.name:
                        ders = v.name[22:33]
                        sinif = v.name[34:-4]
                        if sinif == 'ERP_LAB':
                            sinif = 'ERP-LAB'
                        assign_list.append([d, t, ders, sinif])

    ass_list = []
    for course_name in course:
        day = [i[:2] for i in assign_list if course_name in i[2]][0][0]
        slot = [i[:2] for i in assign_list if course_name in i[2]][0][1]
        classrom_list = [i[-1] for i in assign_list if course_name in i[2]]
        ass_list.append([day, slot, course_name, classrom_list])

    isim = []
    for d in days:
        for t in slots:
            a_list = []
            for i in ass_list:
                if i[0] == d and i[1] == t:
                    a_list.append(i[2] + ' ' + " ".join(i[3]))

            isim.append([d, t, a_list])

    context = {
        'limit_same_time_2': limit_same_time_2,
        'limit_same_time_3': limit_same_time_3,
        'limit_same_time_4': limit_same_time_4,
        'limit_pespese_2': limit_pespese_2,
        'limit_pespese_3': limit_pespese_3,
        'model_sonuc': isim,
        'days': days,
        'slots': slots,
        'solution_time': solution_time

    }

    return render(request, 'schedule.html', context=context)


########################################################################################################################
# Decribe 2'de ortak derslerin dosyaları txt olarak çekildi, şimdilik bunların bilgisini göstermiyoruz.
# Sadece deneme için.


########################################################################################################################
# Decribe 1'de sadece excel dosyasını aldık, bunların bilgilerini de gösteriyoruz.
def describe(request):
    myfile = request.FILES['excel_file']

    fs = FileSystemStorage()
    if FileSystemStorage.exists(fs, myfile.name):
        FileSystemStorage.delete(fs, myfile.name)
    filename = fs.save(myfile.name, myfile)

    file = 'media/' + str(myfile.name)

    # GÜNLER VE SAATLER
    days_slots = pd.read_excel(file, usecols="AI:AJ", skiprows=14, nrows=10)
    days = days_slots["DAYS"].dropna().values.astype(int)  ##############
    slots = days_slots["TIMEINTERVAL"].dropna().values.astype(int)  #############

    # DERSLER
    courses_and_capacities = pd.read_excel(file, usecols="B:D")
    courses_and_capacities.drop(courses_and_capacities.index[0], inplace=True)
    courses_and_capacities.dropna(inplace=True)
    course = courses_and_capacities["COURSE \nNO"].values  ###############
    course_name_dict = dict(zip(course, courses_and_capacities["ALL COURSES"]))
    course_name_list = list(zip(course, courses_and_capacities["ALL COURSES"]))
    course_capacity_dict = dict(zip(course, courses_and_capacities["CAPACITY OF COURSES"].values))  ##############

    # SINIFLAR
    classroom_and_capacities = pd.read_excel(file, usecols="AJ:AL")
    classroom_and_capacities.drop(classroom_and_capacities.index[0], inplace=True)
    classroom_and_capacities.dropna(inplace=True)
    classroom = classroom_and_capacities["CLASSROOMS"].values  ##############
    classroom_capacity_dict = dict(zip(classroom, classroom_and_capacities["Capacity"].values))  ############
    classroom_capacity_list = list(zip(classroom, classroom_and_capacities["Capacity"].values))  ############

    # AYNI ANDA OLACAK DERSLER( Gr1 ve Gr2 gibi)
    same_time_courses = pd.read_excel(file, usecols="BF:BG")[:20]
    same_time_courses.drop(same_time_courses.index[0], inplace=True)
    same_time_courses.dropna(inplace=True)
    same_time_courses = same_time_courses.values  ##################

    # İKİLİ ORTAK DERSLER
    common_two = pd.read_excel(file, usecols="BN:BP", header=0)
    common_two.drop(common_two.index[0], inplace=True)
    common_two.dropna(inplace=True)

    # ÜÇLÜ ORTAK DERSLER
    common_three = pd.read_excel(file, usecols="BS:BV", header=0)
    common_three.drop(common_three.index[0], inplace=True)
    common_three.dropna(inplace=True)

    # DÖRTLÜ ORTAK DERSLER
    common_four = pd.read_excel(file, usecols="BY:CC", header=0)
    common_four.drop(common_four.index[0], inplace=True)
    common_four.dropna(inplace=True)

    # BİRİNCİ SINIF DERSLERİ
    class_1 = pd.read_excel(file, usecols="CH", header=0)[:35]
    class_1.drop(class_1.index[0], inplace=True)
    class_1.dropna(inplace=True)

    # İKİNCİ SINIF DERSLERİ
    class_2 = pd.read_excel(file, usecols="CJ", header=0)[:35]
    class_2.drop(class_2.index[0], inplace=True)
    class_2.dropna(inplace=True)

    # ÜÇÜNCÜ SINIF DERSLERİ
    class_3 = pd.read_excel(file, usecols="CL", header=0)[:35]
    class_3.drop(class_3.index[0], inplace=True)
    class_3.dropna(inplace=True)

    # DÖRDÜNCÜ SINIF DERSLERİ
    class_4 = pd.read_excel(file, usecols="CN", header=0)[:35]
    class_4.drop(class_4.index[0], inplace=True)
    class_4.dropna(inplace=True)

    # DERS VE SINIF UYGUNLUK MATRİSİ
    availability_table = pd.read_excel(file, usecols="F:P", header=0)
    availability_table.drop(availability_table.index[0], inplace=True)
    availability_table.dropna(inplace=True)
    availability_matrix = pd.DataFrame(availability_table.values[:, 1:], index=availability_table.values[:, 0],
                                       columns=classroom)  ##############

    # MÜSAİT ASİSTAN SAYISI
    number_available_assistant = pd.read_excel(file, usecols="AQ:AV")
    number_available_assistant.drop(number_available_assistant.index[0], inplace=True)
    number_available_assistant.dropna(inplace=True)
    number_available_assistant_matrix = pd.DataFrame(number_available_assistant.values[:, 1:], index=slots,
                                                     columns=days)  ###############

    # SINAV KOYULMAYACAK GÜN VE SAATLER
    servis_dersleri = pd.read_excel(file, usecols="EH:EI")
    servis_dersleri.drop(servis_dersleri.index[0], inplace=True)
    servis_dersleri.dropna(inplace=True)
    servis_dersleri = servis_dersleri.values.astype(int)  ##############

    # BU KISIMA DESCRIBE SAYFASINDA GEREK YOK. HATTA BU KISIM DESCRIBE SAYFASINDAN FORM İLE ÇEKİLEBİLİR. İNŞ CNM YA
    # LİMİTLERİN TANIMLANMASI
    """
    limit_same_time_2 = 0
    limit_same_time_3 = 10
    limit_same_time_4 = 10
    limit_pespese_2 = 10
    limit_pespese_3 = 10

    # ORTAK DERS ALANLAR

    same_time_2 = common_two.values[common_two.values[:, 2] > limit_same_time_2][:, :2]
    same_time_3 = common_three.values[common_three.values[:, 3] > limit_same_time_3][:, :3]
    same_time_4 = common_four.values[common_four.values[:, 4] > limit_same_time_4][:, :4]
    pespese_2 = common_two.values[common_two.values[:, 2] > limit_pespese_2][:, :2]
    pespese_3 = common_three.values[common_three.values[:, 3] > limit_pespese_3][:, :3]
    """

    context = {
        'course_list': course_name_list,
        'classroom_list': classroom_capacity_list,
        'file': myfile.name,
        'days': len(days),
        'slots': len(slots),
        'servis_dersleri': servis_dersleri
    }

    return render(request, 'describe.html', context=context)


########################################################################################################################
# Schedule 2 de DECOMPOSE YAPILMADI, tüm model direkt olarak çözüldü. Yavaş olan model bu.
def schedule_2(request):
    file = 'media/' + request.POST.get('file_name')

    limit_same_time_2 = int(request.POST.get('limit_same_time_2'))
    limit_same_time_3 = int(request.POST.get('limit_same_time_3'))
    limit_same_time_4 = int(request.POST.get('limit_same_time_4'))
    limit_pespese_2 = int(request.POST.get('limit_pespese_2'))
    limit_pespese_3 = int(request.POST.get('limit_pespese_3'))

    # GÜNLER VE SAATLER
    days_slots = pd.read_excel(file, usecols="AI:AJ", skiprows=14, nrows=10)
    days = days_slots["DAYS"].dropna().values.astype(int)  ##############
    slots = days_slots["TIMEINTERVAL"].dropna().values.astype(int)  #############

    # DERSLER
    courses_and_capacities = pd.read_excel(file, usecols="B:D")
    courses_and_capacities.drop(courses_and_capacities.index[0], inplace=True)
    courses_and_capacities.dropna(inplace=True)
    course = courses_and_capacities["COURSE \nNO"].values  ###############
    course_name_dict = dict(zip(course, courses_and_capacities["ALL COURSES"]))
    course_capacity_dict = dict(zip(course, courses_and_capacities["CAPACITY OF COURSES"].values))  ##############

    # SINIFLAR
    classroom_and_capacities = pd.read_excel(file, usecols="AJ:AL")
    classroom_and_capacities.drop(classroom_and_capacities.index[0], inplace=True)
    classroom_and_capacities.dropna(inplace=True)
    classroom = classroom_and_capacities["CLASSROOMS"].values  ##############
    classroom_capacity_dict = dict(zip(classroom, classroom_and_capacities["Capacity"].values))  ############

    # AYNI ANDA OLACAK DERSLER( Gr1 ve Gr2 gibi)
    same_time_courses = pd.read_excel(file, usecols="BF:BG")[:20]
    same_time_courses.drop(same_time_courses.index[0], inplace=True)
    same_time_courses.dropna(inplace=True)
    same_time_courses = same_time_courses.values  ##################

    # İKİLİ ORTAK DERSLER
    common_two = pd.read_excel(file, usecols="BN:BP", header=0)
    common_two.drop(common_two.index[0], inplace=True)
    common_two.dropna(inplace=True)

    # ÜÇLÜ ORTAK DERSLER
    common_three = pd.read_excel(file, usecols="BS:BV", header=0)
    common_three.drop(common_three.index[0], inplace=True)
    common_three.dropna(inplace=True)

    # DÖRTLÜ ORTAK DERSLER
    common_four = pd.read_excel(file, usecols="BY:CC", header=0)
    common_four.drop(common_four.index[0], inplace=True)
    common_four.dropna(inplace=True)

    # BİRİNCİ SINIF DERSLERİ
    class_1 = pd.read_excel(file, usecols="CH", header=0)[:35]
    class_1.drop(class_1.index[0], inplace=True)
    class_1.dropna(inplace=True)

    # İKİNCİ SINIF DERSLERİ
    class_2 = pd.read_excel(file, usecols="CJ", header=0)[:35]
    class_2.drop(class_2.index[0], inplace=True)
    class_2.dropna(inplace=True)

    # ÜÇÜNCÜ SINIF DERSLERİ
    class_3 = pd.read_excel(file, usecols="CL", header=0)[:35]
    class_3.drop(class_3.index[0], inplace=True)
    class_3.dropna(inplace=True)

    # DÖRDÜNCÜ SINIF DERSLERİ
    class_4 = pd.read_excel(file, usecols="CN", header=0)[:35]
    class_4.drop(class_4.index[0], inplace=True)
    class_4.dropna(inplace=True)

    # DERS VE SINIF UYGUNLUK MATRİSİ
    availability_table = pd.read_excel(file, usecols="F:P", header=0)
    availability_table.drop(availability_table.index[0], inplace=True)
    availability_table.dropna(inplace=True)
    availability_matrix = pd.DataFrame(availability_table.values[:, 1:], index=availability_table.values[:, 0],
                                       columns=classroom)  ##############

    # MÜSAİT ASİSTAN SAYISI
    number_available_assistant = pd.read_excel(file, usecols="AQ:AV")
    number_available_assistant.drop(number_available_assistant.index[0], inplace=True)
    number_available_assistant.dropna(inplace=True)
    number_available_assistant_matrix = pd.DataFrame(number_available_assistant.values[:, 1:], index=slots,
                                                     columns=days)  ###############

    # SINAV KOYULMAYACAK GÜN VE SAATLER
    servis_dersleri = pd.read_excel(file, usecols="EH:EI")
    servis_dersleri.drop(servis_dersleri.index[0], inplace=True)
    servis_dersleri.dropna(inplace=True)
    servis_dersleri = servis_dersleri.values.astype(int)  ##############

    # ORTAK DERS ALANLAR

    same_time_2 = common_two.values[common_two.values[:, 2] > limit_same_time_2][:, :2]
    same_time_3 = common_three.values[common_three.values[:, 3] > limit_same_time_3][:, :3]
    same_time_4 = common_four.values[common_four.values[:, 4] > limit_same_time_4][:, :4]
    pespese_2 = common_two.values[common_two.values[:, 2] > limit_pespese_2][:, :2]
    pespese_3 = common_three.values[common_three.values[:, 3] > limit_pespese_3][:, :3]

    problem = pulp.LpProblem('Exam_Assigment_Problem', pulp.LpMinimize)
    X_assign = pulp.LpVariable.dicts('Assign_with_classroom', (course, classroom, days, slots), lowBound=0, upBound=1,
                                     cat=pulp.LpBinary)
    Z_assign = pulp.LpVariable.dicts('Assign_without_classroom', (course, days, slots), lowBound=0, upBound=1,
                                     cat=pulp.LpBinary)

    # (1) Bir sınıfa bir günde ve bir intervalda birden fazla ders atanmasın
    for j in classroom:
        for d in days:
            for t in slots:
                problem += pulp.lpSum([X_assign[i][j][d][t] for i in course]) <= 1

                # (2) Her bir ders bir güne ve bir saate atanmalı, ders boşta kalmasın kısıtı.
    for i in course:
        problem += pulp.lpSum([Z_assign[i][d][t] for d in days for t in slots]) == 1

    # (3) Bir dersin atandığım tüm sınıfları kapasitelerinin toplamı dersin kapasitesinden büyük olmalıdır.
    for i in course:
        problem += pulp.lpSum(
            [X_assign[i][j][d][t] * classroom_capacity_dict[j] for j in classroom for d in days for t in slots]) >= \
                   course_capacity_dict[i]

        # (4) Her ders her sınıfta olamaz, bazı sınavlar sadece bazı sınıflarda olabilir.
    for i in course:
        for j in classroom:
            problem += pulp.lpSum([X_assign[i][j][d][t] for d in days for t in slots]) <= availability_matrix[j][i]

    """
    # (5) Friday günü 3. slota ders koyma (cuma namazı) #Bu kısıt servis derslerinin içinde zaten var. 
    problem += pulp.lpSum([Z_assign[i][5][3] for i in course]) == 0
    """

    # (6) Aynı gün ve aynı slotta olması gereken dersleri aynı zamana koy.
    for i0, i1 in same_time_courses:
        for d in days:
            for t in slots:
                problem += Z_assign[i0][d][t] - Z_assign[i1][d][t] == 0

                # (7) Not same time course'du ama şimdilk gerek yok.

        # (8) İkili ortak dersler limitten fazla ise aynı güne koyma.
    for i0, i1 in same_time_2:
        for d in days:
            for t in slots:
                problem += Z_assign[i0][d][t] + Z_assign[i1][d][t] <= 1

    # (9) Üçlü ortak dersler limitten fazla ise aynı güne koyma.
    for i0, i1, i2 in same_time_3:
        for d in days:
            for t in slots:
                problem += Z_assign[i0][d][t] + Z_assign[i1][d][t] + Z_assign[i2][d][t] <= 2

    # (10) Dörtlü ortak dersler limitten fazla ise aynı güne koyma.
    for i0, i1, i2, i3 in same_time_4:
        for d in days:
            for t in slots:
                problem += Z_assign[i0][d][t] + Z_assign[i1][d][t] + Z_assign[i2][d][t] + Z_assign[i3][d][t] <= 3

    # (11) 2'li ortak derslerden limiti geçenleri peşpeşe yazma.
    for i0, i1 in pespese_2:
        for d in days:
            for t in slots:
                if t + 1 in slots:
                    problem += Z_assign[i0][d][t] + Z_assign[i1][d][t + 1] <= 1
                    problem += Z_assign[i1][d][t] + Z_assign[i0][d][t + 1] <= 1

    # (12) 3'lü ortak derslerden limiti geçenleri peşpeşe yazma.
    for i0, i1, i2 in pespese_3:
        for d in days:
            for t in slots:
                if t + 1 in slots and t + 2 in slots:
                    problem += Z_assign[i0][d][t] + Z_assign[i1][d][t + 1] + Z_assign[i2][d][t + 2] <= 2
                    problem += Z_assign[i0][d][t] + Z_assign[i2][d][t + 1] + Z_assign[i1][d][t + 2] <= 2
                    problem += Z_assign[i1][d][t] + Z_assign[i0][d][t + 1] + Z_assign[i2][d][t + 2] <= 2
                    problem += Z_assign[i1][d][t] + Z_assign[i2][d][t + 1] + Z_assign[i0][d][t + 2] <= 2
                    problem += Z_assign[i2][d][t] + Z_assign[i0][d][t + 1] + Z_assign[i1][d][t + 2] <= 2
                    problem += Z_assign[i2][d][t] + Z_assign[i1][d][t + 1] + Z_assign[i0][d][t + 2] <= 2

    # (13) Servis derslerinin olduğu günün slotun sınav koyma.
    for d, t in servis_dersleri:
        problem += pulp.lpSum([Z_assign[i][d][t] for i in course]) == 0

    # (14) İki değişkenin bağlantısını aşağıdaki kısıtlarla sağlaycağız.
    for i in course:
        for d in days:
            for t in slots:
                problem += pulp.lpSum([X_assign[i][j][d][t] for j in classroom]) >= Z_assign[i][d][t]

                # (15) İki değişkenin bağlantısını aşağıdaki kısıtlarla sağlaycağız -2.
    for i in course:
        for d in days:
            for t in slots:
                problem += pulp.lpSum([X_assign[i][j][d][t] for j in classroom]) <= 5 * Z_assign[i][d][t]

                # (16) Assistant satısına göre sınıflara atama yap.
    for d in days:
        for t in slots:
            problem += pulp.lpSum([X_assign[i][j][d][t] for j in classroom for i in course]) <= \
                       number_available_assistant_matrix[d][t]

    problem += pulp.lpSum([X_assign[i][j][d][t] for i in course for j in classroom for d in days for t in slots])
    start = time.time()
    problem.solve()
    end = time.time()
    optimal_check = pulp.LpStatus[problem.status]
    solution_time = round((end - start))
    assign_list = []
    for d in days:
        for t in slots:
            # print('Day:', d, ' Slot:',t )
            for v in problem.variables():
                if v.value() == 1:
                    if "_" + str(d) + "_" + str(t) in v.name and 'with_' in v.name:
                        ders = v.name[22:33]
                        sinif = v.name[34:-4]
                        if sinif == 'ERP_LAB':
                            sinif = 'ERP-LAB'
                        assign_list.append([d, t, ders, sinif])

    ass_list = []
    for course_name in course:
        day = [i[:2] for i in assign_list if course_name in i[2]][0][0]
        slot = [i[:2] for i in assign_list if course_name in i[2]][0][1]
        classrom_list = [i[-1] for i in assign_list if course_name in i[2]]
        ass_list.append([day, slot, course_name, classrom_list])

    isim = []
    for d in days:
        for t in slots:
            a_list = []
            for i in ass_list:
                if i[0] == d and i[1] == t:
                    a_list.append(i[2] + ' ' + " ".join(i[3]))

            isim.append([d, t, a_list])

    context = {
        'limit_same_time_2': limit_same_time_2,
        'limit_same_time_3': limit_same_time_3,
        'limit_same_time_4': limit_same_time_4,
        'limit_pespese_2': limit_pespese_2,
        'limit_pespese_3': limit_pespese_3,
        'model_sonuc': isim,
        'days': days,
        'slots': slots,
        'solution_time': solution_time,
        'optimal_check': optimal_check

    }

    return render(request, 'schedule_2.html', context=context)


########################################################################################################################
# Schedule 3 DECOMPOSE yapıldı. Bunların üzerine ortak ders listesi eklenecek.
def schedule_3(request):
    print('start')
    ############
    file = 'media/' + request.POST.get('file_name')

    limit_same_time_2 = int(request.POST.get('limit_same_time_2'))
    limit_same_time_3 = int(request.POST.get('limit_same_time_3'))
    limit_same_time_4 = int(request.POST.get('limit_same_time_4'))
    limit_pespese_2 = int(request.POST.get('limit_pespese_2'))
    limit_pespese_3 = int(request.POST.get('limit_pespese_3'))

    # GÜNLER VE SAATLER
    days_slots = pd.read_excel(file, usecols="AI:AJ", skiprows=14, nrows=10)
    days = days_slots["DAYS"].dropna().values.astype(int)  ##############
    slots = days_slots["TIMEINTERVAL"].dropna().values.astype(int)  #############

    # DERSLER
    courses_and_capacities = pd.read_excel(file, usecols="B:D")
    courses_and_capacities.drop(courses_and_capacities.index[0], inplace=True)
    courses_and_capacities.dropna(inplace=True)
    course = courses_and_capacities["COURSE \nNO"].values  ###############
    course_name_dict = dict(zip(course, courses_and_capacities["ALL COURSES"]))
    course_capacity_dict = dict(zip(course, courses_and_capacities["CAPACITY OF COURSES"].values))  ##############

    # SINIFLAR
    classroom_and_capacities = pd.read_excel(file, usecols="AJ:AL")
    classroom_and_capacities.drop(classroom_and_capacities.index[0], inplace=True)
    classroom_and_capacities.dropna(inplace=True)
    classroom = classroom_and_capacities["CLASSROOMS"].values  ##############
    classroom_capacity_dict = dict(zip(classroom, classroom_and_capacities["Capacity"].values))  ############

    # AYNI ANDA OLACAK DERSLER( Gr1 ve Gr2 gibi)
    same_time_courses = pd.read_excel(file, usecols="BF:BG")[:20]
    same_time_courses.drop(same_time_courses.index[0], inplace=True)
    same_time_courses.dropna(inplace=True)
    same_time_courses = same_time_courses.values  ##################


    # BİRİNCİ SINIF DERSLERİ
    class_1 = pd.read_excel(file, usecols="CH", header=0)[:35]
    class_1.drop(class_1.index[0], inplace=True)
    class_1.dropna(inplace=True)

    # İKİNCİ SINIF DERSLERİ
    class_2 = pd.read_excel(file, usecols="CJ", header=0)[:35]
    class_2.drop(class_2.index[0], inplace=True)
    class_2.dropna(inplace=True)

    # ÜÇÜNCÜ SINIF DERSLERİ
    class_3 = pd.read_excel(file, usecols="CL", header=0)[:35]
    class_3.drop(class_3.index[0], inplace=True)
    class_3.dropna(inplace=True)

    # DÖRDÜNCÜ SINIF DERSLERİ
    class_4 = pd.read_excel(file, usecols="CN", header=0)[:35]
    class_4.drop(class_4.index[0], inplace=True)
    class_4.dropna(inplace=True)

    # DERS VE SINIF UYGUNLUK MATRİSİ
    availability_table = pd.read_excel(file, usecols="F:P", header=0)
    availability_table.drop(availability_table.index[0], inplace=True)
    availability_table.dropna(inplace=True)
    availability_matrix = pd.DataFrame(availability_table.values[:, 1:], index=availability_table.values[:, 0],
                                       columns=classroom)  ##############

    # MÜSAİT ASİSTAN SAYISI
    number_available_assistant = pd.read_excel(file, usecols="AQ:AV")
    number_available_assistant.drop(number_available_assistant.index[0], inplace=True)
    number_available_assistant.dropna(inplace=True)
    number_available_assistant_matrix = pd.DataFrame(number_available_assistant.values[:, 1:], index=slots,
                                                     columns=days)  ###############

    # SINAV KOYULMAYACAK GÜN VE SAATLER
    servis_dersleri = pd.read_excel(file, usecols="EH:EI")
    servis_dersleri.drop(servis_dersleri.index[0], inplace=True)
    servis_dersleri.dropna(inplace=True)
    servis_dersleri = servis_dersleri.values.astype(int)  ##############

    """

  # İKİLİ ORTAK DERSLER
    common_two = pd.read_excel(file, usecols="BN:BP", header=0)
    common_two.drop(common_two.index[0], inplace=True)
    common_two.dropna(inplace=True)

    # ÜÇLÜ ORTAK DERSLER
    common_three = pd.read_excel(file, usecols="BS:BV", header=0)
    common_three.drop(common_three.index[0], inplace=True)
    common_three.dropna(inplace=True)

    # DÖRTLÜ ORTAK DERSLER
    common_four = pd.read_excel(file, usecols="BY:CC", header=0)
    common_four.drop(common_four.index[0], inplace=True)
    common_four.dropna(inplace=True)"""


    ###########
    # Ders Listelerinin Dosyaları
    onlyfiles = []
    for file in request.FILES.getlist('common_course_file'):
        myfile_txt = file

        fs_txt = FileSystemStorage()
        if FileSystemStorage.exists(fs_txt, myfile_txt.name):
            FileSystemStorage.delete(fs_txt, myfile_txt.name)

        filename = fs_txt.save(myfile_txt.name, myfile_txt)
        file_txt = 'media/' + str(myfile_txt.name)
        onlyfiles.append(file_txt)

    course_student_dict = {}
    for file in onlyfiles:
        if file[-16:-5] in course:
            f = open(file, "r")
            a = f.read().strip().split('\n')
            course_student_dict[file[-16:-5]] = a

    course_list = list(course_student_dict.keys())

    # İkililer
    same_time_2 = []

    for i in range(len(course_list)):
        for j in range(i + 1, len(course_list)):
            num = len(set(course_student_dict[course_list[i]]) & set(course_student_dict[course_list[j]]))
            if num > 0:
                same_time_2.append((course_list[i], course_list[j], num))

    # Üçlüler
    same_time_3 = []

    for i in range(len(course_list)):
        for j in range(i + 1, len(course_list)):
            for k in range(j + 1, len(course_list)):
                num = len(set(course_student_dict[course_list[i]]) & set(course_student_dict[course_list[j]]) & set(
                    course_student_dict[course_list[k]]))
                if num > 0:
                    same_time_3.append((course_list[i], course_list[j], course_list[k], num))

    # Dörtlüler
    same_time_4 = []

    for i in range(len(course_list)):
        for j in range(i + 1, len(course_list)):
            for k in range(j + 1, len(course_list)):
                for t in range(k + 1, len(course_list)):
                    num = len(
                        set(course_student_dict[course_list[i]]) & set(course_student_dict[course_list[j]]) & set(
                            course_student_dict[course_list[k]]) & set(course_student_dict[course_list[t]]))
                    if num > 0:
                        same_time_4.append((course_list[i], course_list[j], course_list[k], course_list[t], num))

    common_two = pd.DataFrame(same_time_2)

    common_three = pd.DataFrame(same_time_3)

    common_four = pd.DataFrame(same_time_4)

    # ORTAK DERS ALANLAR

    same_time_2 = common_two.values[common_two.values[:, 2] > limit_same_time_2][:, :2]
    same_time_3 = common_three.values[common_three.values[:, 3] > limit_same_time_3][:, :3]
    same_time_4 = common_four.values[common_four.values[:, 4] > limit_same_time_4][:, :4]
    pespese_2 = common_two.values[common_two.values[:, 2] > limit_pespese_2][:, :2]
    pespese_3 = common_three.values[common_three.values[:, 3] > limit_pespese_3][:, :3]




    problem = pulp.LpProblem('Exam_Assigment_Problem', pulp.LpMinimize)
    Z_assign = pulp.LpVariable.dicts('Assign_without_classroom', (course, days, slots), lowBound=0, upBound=1,
                                     cat=pulp.LpBinary)

    # (2) Her bir ders bir güne ve bir saate atanmalı, ders boşta kalmasın kısıtı.
    for i in course:
        problem += pulp.lpSum([Z_assign[i][d][t] for d in days for t in slots]) == 1

    # (3) Bir güne ve saate max 5 ders atansın
    for d in days:
        for t in slots:
            problem += pulp.lpSum([Z_assign[i][d][t] for i in course]) <= 5

    # (4) Bir güne ve bir slota atanan derslerin kapasite toplamları 245'yi geçemez.
    for d in days:
        for t in slots:
            problem += pulp.lpSum([Z_assign[i][d][t] * course_capacity_dict[i] for i in course]) <= 245


    # (6) Aynı gün ve aynı slotta olması gereken dersleri aynı zamana koy.
    for i0, i1 in same_time_courses:
        for d in days:
            for t in slots:
                problem += Z_assign[i0][d][t] - Z_assign[i1][d][t] == 0

    # (7) Not same time course'du ama şimdilk gerek yok.

    # (8) İkili ortak dersler limitten fazla ise aynı güne koyma.
    for i0, i1 in same_time_2:
        for d in days:
            for t in slots:
                problem += Z_assign[i0][d][t] + Z_assign[i1][d][t] <= 1

    # (9) Üçlü ortak dersler limitten fazla ise aynı güne koyma.
    for i0, i1, i2 in same_time_3:
        for d in days:
            for t in slots:
                problem += Z_assign[i0][d][t] + Z_assign[i1][d][t] + Z_assign[i2][d][t] <= 2

    # (10) Dörtlü ortak dersler limitten fazla ise aynı güne koyma.
    for i0, i1, i2, i3 in same_time_4:
        for d in days:
            for t in slots:
                problem += Z_assign[i0][d][t] + Z_assign[i1][d][t] + Z_assign[i2][d][t] + Z_assign[i3][d][t] <= 3

    # (11) 2'li ortak derslerden limiti geçenleri peşpeşe yazma.
    for i0, i1 in pespese_2:
        for d in days:
            for t in slots:
                if t + 1 in slots:
                    problem += Z_assign[i0][d][t] + Z_assign[i1][d][t + 1] <= 1
                    problem += Z_assign[i1][d][t] + Z_assign[i0][d][t + 1] <= 1

    # (12) 3'lü ortak derslerden limiti geçenleri peşpeşe yazma.
    for i0, i1, i2 in pespese_3:
        for d in days:
            for t in slots:
                if t + 1 in slots and t + 2 in slots:
                    problem += Z_assign[i0][d][t] + Z_assign[i1][d][t + 1] + Z_assign[i2][d][t + 2] <= 2
                    problem += Z_assign[i0][d][t] + Z_assign[i2][d][t + 1] + Z_assign[i1][d][t + 2] <= 2
                    problem += Z_assign[i1][d][t] + Z_assign[i0][d][t + 1] + Z_assign[i2][d][t + 2] <= 2
                    problem += Z_assign[i1][d][t] + Z_assign[i2][d][t + 1] + Z_assign[i0][d][t + 2] <= 2
                    problem += Z_assign[i2][d][t] + Z_assign[i0][d][t + 1] + Z_assign[i1][d][t + 2] <= 2
                    problem += Z_assign[i2][d][t] + Z_assign[i1][d][t + 1] + Z_assign[i0][d][t + 2] <= 2

    # (13) Servis derslerinin olduğu günün slotun sınav koyma.
    for d, t in servis_dersleri:
        problem += pulp.lpSum([Z_assign[i][d][t] for i in course]) == 0

    problem += 0

    start = time.time()
    problem.solve()
    end = time.time()
    optimal_check = pulp.LpStatus[problem.status]
    solution_time = round((end - start))


    assignment = []
    for c in course:
        for d in days:
            for t in slots:
                if Z_assign[c][d][t].varValue == 1:
                    assignment.append([c, d, t])

    infeasible_list = []
    classroom_assign_list = list()
    for d in days:
        for t in slots:
            course_list = [assignment[i][0] for i in range(len(assignment)) if assignment[i][1:] == [d, t]]
            if len(course_list) != 0:
                problem_2 = pulp.LpProblem('Second_Step', pulp.LpMinimize)
                X_assign = pulp.LpVariable.dicts('Assign_with_classroom', (course_list, classroom), lowBound=0,
                                                 upBound=1, cat=pulp.LpBinary)
                problem_2 += pulp.lpSum([X_assign[i][j] for j in classroom for i in course_list])
                # (1) Her sınıfa MAX bir ders atansın.
                for j in classroom:
                    problem_2 += pulp.lpSum([X_assign[i][j] for i in course_list]) <= 1

                # (2) Bir ders MİN bir sınıfa atansın.
                for i in course_list:
                    problem_2 += pulp.lpSum([X_assign[i][j] for j in classroom]) >= 1

                # (3) Dersin atandığı sınıfların kapasitelerinin toplamı dersin kapasitesiden büyük olmalı.
                for i in course_list:
                    problem_2 += pulp.lpSum([X_assign[i][j] * classroom_capacity_dict[j] for j in classroom]) >= \
                                 course_capacity_dict[i]

                # (4) Her ders her sınıfta olamaz, bazı sınavlar sadece bazı sınıflarda olabilir.
                for i in course_list:
                    for j in classroom:
                        problem_2 += X_assign[i][j] <= availability_matrix[j][i]

                problem_2.solve()
                if pulp.LpStatus[problem_2.status] != "Optimal":
                    infeasible_list.append(course_list)
                    infeasible_list = np.array(infeasible_list, dtype="object")
                    print(pulp.LpStatus[problem_2.status])
                for j in course_list:
                    for c in classroom:
                        if X_assign[j][c].varValue == 1:
                            classroom_assign_list.append([j, c])

    while len(infeasible_list) != 0:
        # (14) Infeasible list kısıtı
        for i in infeasible_list:
            if len(i) == 4:
                for d in days:
                    for t in slots:
                        problem += Z_assign[i[0]][d][t] + Z_assign[i[1]][d][t] + Z_assign[i[2]][d][t] + \
                                   Z_assign[i[3]][d][t] <= 3
            elif len(i) == 3:
                for d in days:
                    for t in slots:
                        problem += Z_assign[i[0]][d][t] + Z_assign[i[1]][d][t] + Z_assign[i[2]][d][t] <= 2

            elif len(i) == 2:
                for d in days:
                    for t in slots:
                        problem += Z_assign[i[0]][d][t] + Z_assign[i[1]][d][t] <= 1
            elif len(i) == 5:
                for d in days:
                    for t in slots:
                        problem += Z_assign[i[0]][d][t] + Z_assign[i[1]][d][t] + Z_assign[i[2]][d][t] + \
                                   Z_assign[i[3]][d][t] + Z_assign[i[4]][d][t] <= 4
            else:
                print("We Have a Problem....")

        print('problem solving')
        problem.solve()
        print('problem solved')

        assignment = []
        for c in course:
            for d in days:
                for t in slots:
                    if Z_assign[c][d][t].varValue == 1:
                        assignment.append([c, d, t])

        infeasible_list = []
        classroom_assign_list = list()
        for d in days:
            for t in slots:
                course_list = [assignment[i][0] for i in range(len(assignment)) if assignment[i][1:] == [d, t]]
                if len(course_list) != 0:
                    problem_2 = pulp.LpProblem('Second_Step', pulp.LpMinimize)
                    X_assign = pulp.LpVariable.dicts('Assign_with_classroom', (course_list, classroom), lowBound=0,
                                                     upBound=1, cat=pulp.LpBinary)
                    problem_2 += pulp.lpSum([X_assign[i][j] for j in classroom for i in course_list])
                    # (1) Her sınıfa MAX bir ders atansın.
                    for j in classroom:
                        problem_2 += pulp.lpSum([X_assign[i][j] for i in course_list]) <= 1

                    # (2) Bir ders MİN bir sınıfa atansın.
                    for i in course_list:
                        problem_2 += pulp.lpSum([X_assign[i][j] for j in classroom]) >= 1

                        # (3) Dersin atandığı sınıfların kapasitelerinin toplamı dersin kapasitesiden büyük olmalı.
                    for i in course_list:
                        problem_2 += pulp.lpSum([X_assign[i][j] * classroom_capacity_dict[j] for j in classroom]) >= \
                                     course_capacity_dict[i]

                    # (4) Her ders her sınıfta olamaz, bazı sınavlar sadece bazı sınıflarda olabilir.
                    for i in course_list:
                        for j in classroom:
                            problem_2 += X_assign[i][j] <= availability_matrix[j][i]

                    problem_2.solve()
                    if pulp.LpStatus[problem_2.status] != "Optimal":
                        infeasible_list.append(course_list)
                        infeasible_list = np.array(infeasible_list, dtype="object")
                        print(pulp.LpStatus[problem_2.status])
                    for j in course_list:
                        for c in classroom:
                            if X_assign[j][c].varValue == 1:
                                classroom_assign_list.append([j, c])

    ass_list = []
    for i in assignment:
        class_list = []
        for j in classroom_assign_list:
            if i[0] == j[0]:
                class_list.append(j[1])
        ass_list.append([i[1], i[2], i[0], class_list])

    isim = []
    for d in days:
        for t in slots:
            # print(d,t)
            a_list = []
            for i in ass_list:
                if i[0] == d and i[1] == t:
                    a_list.append(i[2] + ' ' + " ".join(i[3]))

            isim.append([d, t, a_list])

    context = {
        'limit_same_time_2': limit_same_time_2,
        'limit_same_time_3': limit_same_time_3,
        'limit_same_time_4': limit_same_time_4,
        'limit_pespese_2': limit_pespese_2,
        'limit_pespese_3': limit_pespese_3,
        'model_sonuc': isim,
        'days': days,
        'slots': slots,
        'solution_time': solution_time,
        'optimal_check': optimal_check

    }

    return render(request, 'schedule_3.html', context=context)