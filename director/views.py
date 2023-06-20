#director APP

from django.shortcuts import render
from django.shortcuts import render,HttpResponse,redirect
import json
from manager import models
from django.http import JsonResponse
from django.forms.models import model_to_dict
from django.db.models import Q

def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    elif request.method == "POST":
        ret = {'status': True, 'error': None}
        try:
            user_code = request.POST.get('sec_username',None)    #沒有则为空
            password = request.POST.get('sec_password',None)
            remember = request.POST.get('sec_remember',None)   #这是Ture 记住密码or falase不记住
            #print("记住密码:", remember)
            obj = models.UserTable.objects.filter(user_code=user_code,user_type='2').first()  #找到用户  且用户为系主任
            if obj:
                if obj.user_stat=="1":
                    if obj.user_password==password:
                        request.session['is_login'] = True
                        request.session['user_code'] = user_code
                        request.session['user_type'] ='2'             #在session写入用户的类型  给与不同用户不同的权限
                        request.session.set_expiry(24*60*60)  #一天免登陆
                        if remember=="True":
                            request.session.set_expiry(14*24*60*60)    #两周内免登陆
                            print("设置了一小时免登陆")
                    else:
                        ret['status'] = False
                        ret['error'] = "密码错误请重新输入"
                else:
                    ret['status'] = False
                    ret['error'] = "教务号已冻结请联系管理员"
            else:
                ret['status'] = False
                ret['error'] = "教务号不存在请联系管理员注册"
        except Exception as e:
            ret['status'] = False
            ret['error'] = '未知错误'
        return HttpResponse(json.dumps(ret))
    else:
        return HttpResponse("该页面还在准备中@@")


def home(request):
    if request.method == "GET":
        # session中获取值
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '2':
            #登录成功后的操作
            user_code=request.session['user_code']   #用户账号
            obj = models.UserTable.objects.filter(user_code=user_code).first()  #查找用户相关信息
            return render(request,'DirHome.html',{'user_name':obj.user_name})
        else:
            return render(request, 'login.html')
    else:
        return HttpResponse("该页面还在准备中@@")


def manage(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '2':
            return render(request, 'DirManage.html')
        else:
            return render(request, 'login.html')


    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取系主任的账号
        login_dpartment_name_id=models.UserTable.objects.filter(user_code=login_user_code).first().dpartment_name_id  #获取系主任所属的系号
        return_data = {'status': True, 'data': None}   #返回的数据初始化
        operate = request.POST.get('operate', None)  # 获取需要的操作


        if operate=="search":
            find_user_name=request.POST.get('find_user_name', None)   #用户名
            select_stat=request.POST.get('select_stat', None)         #0表示全部  1表示正常 2冻结
            select_type=request.POST.get('select_type', None)         #选择类型 0表示学生 1表示老师 2表示全部
            dic_user_list=[]                                            #找到数据后返回的列表
            if find_user_name=="":
                if select_stat=="0":
                    if select_type=="2":
                        obj = models.UserTable.objects.filter(Q(user_type=1)|Q(user_type=0),dpartment_name_id=login_dpartment_name_id)  #查找所有该系老师和学生的信息
                    else:
                        obj = models.UserTable.objects.filter(user_type=select_type,dpartment_name_id=login_dpartment_name_id)
                else:
                    if select_type == "2":
                        obj = models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),user_stat=select_stat,dpartment_name_id=login_dpartment_name_id)
                    else:
                        obj = models.UserTable.objects.filter(user_type=select_type,user_stat=select_stat,dpartment_name_id=login_dpartment_name_id)
            else:
                if select_stat=="0":
                    if select_type=="2":
                        obj = models.UserTable.objects.filter(Q(user_type=1)|Q(user_type=0),user_name=find_user_name,dpartment_name_id=login_dpartment_name_id)  #查找所有该系老师和学生的信息
                    else:
                        obj = models.UserTable.objects.filter(user_type=select_type,user_name=find_user_name,dpartment_name_id=login_dpartment_name_id)
                else:
                    if select_type == "2":
                        obj = models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),user_name=find_user_name,user_stat=select_stat,dpartment_name_id=login_dpartment_name_id)
                    else:
                        obj = models.UserTable.objects.filter(user_type=select_type,user_name=find_user_name,user_stat=select_stat,dpartment_name_id=login_dpartment_name_id)
            if len(obj)==0:
                return_data['status']=False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)       #对象数据转字典
                    jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                    dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象

        elif operate=="batch_add":
            batch_csv = request.FILES["batch_csv"]
            if not batch_csv.name.endswith('.csv'):
                return_data['status'] = False
                return_data['data'] = "必须是.csv文件"         #错误原因
                return JsonResponse(return_data, safe=False)
            batch_data = []  # 储存csv数据 校检后的数据
            try:
                file_data = batch_csv.read().decode("utf-8")  # 读取文件
                lines = file_data.split("\n")
                del(lines[0])                            #删除第一行  第一行都为列标注
                for line in lines:
                    line=line.strip()       #去掉回车
                    cell = line.split(",")  # 分成单元格   如果没有
                    if len(cell)==5:
                        if cell[0]=="" or cell[1]=="" or cell[4]=="":      #学号为空  姓名为空  类型为空 则触发异常
                            raise Exception("类型错误", cell)
                        if cell[2]=="":                                    #邮箱和电话可以为空
                            cell[2]=None
                        if cell[3]=="":
                            cell[3]=None
                        if cell[4]=="导师" or cell[4]=="学生":
                            batch_data.append(cell)
                        else:
                            raise Exception("类型错误",cell)
            except:
                return_data['status'] = False
                return_data['data'] = "文件的内容格式不正确"  # 错误原因
                return JsonResponse(return_data, safe=False)
            else:
                for line in batch_data:
                    if len(models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),user_code= line[0]))==0:        #如果用户不存在
                        if line[4]=="导师":
                            models.UserTable.objects.create(user_code=line[0], user_password="123456",dpartment_name_id=login_dpartment_name_id,
                                                          user_name=line[1],user_mail=line[2],user_phone=line[3],user_stat="1",
                                                          user_type="1",stu_num="0",remark=None,op_no=login_user_code)
                        else:
                            models.UserTable.objects.create(user_code=line[0], user_password="123456",dpartment_name_id=login_dpartment_name_id,
                                                          user_name=line[1],user_mail=line[2],user_phone=line[3],user_stat="1",
                                                          user_type="0",stu_num=None,remark=None,op_no=login_user_code)
                dic_user_list = []
                obj = models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),dpartment_name_id=login_dpartment_name_id)
                for line in obj:
                    jsonstr = model_to_dict(line)  # 对象数据转字典
                    jsonstr['dpartment_name'] = line.dpartment_name.dpartement_name  # 更改系的数据 外键操作
                    dic_user_list.append(jsonstr)
                return_data['data'] = dic_user_list
                return JsonResponse(return_data, safe=False)

        elif operate=="add":
            add_user_name=request.POST.get('add_user_name', None)   #用户名
            add_user_code=request.POST.get('add_user_code', None)    #账号
            add_user_mail=request.POST.get('add_user_mail', None)
            add_stu_num=request.POST.get('add_stu_num', None)        #老师指导学生人数
            add_user_phone=request.POST.get('add_user_phone', None)
            add_remark=request.POST.get('add_remark', None)
            check_type=request.POST.get('check_type', None)    #true   则为老师  false 为学生
            if add_user_name=="":
                return_data['status'] = False
                return_data['data'] = "姓名不能不空"
                return JsonResponse(return_data, safe=False)
            if add_user_code=="":
                return_data['status'] = False
                return_data['data'] = "登录账号不能不空"
                return JsonResponse(return_data, safe=False)
            if check_type=="true":
                if add_stu_num=="":
                    return_data['status'] = False
                    return_data['data'] = "指导学生不能为空"
                    return JsonResponse(return_data, safe=False)
            if len(models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),user_code=add_user_code,))>0:
                return_data['status'] = False
                return_data['data'] = "该登录账号已存在"
                return JsonResponse(return_data, safe=False)
            if len(add_user_mail)==0:
                add_user_mail=None
            if len(add_user_phone)==0:
                add_user_phone=None
            if len(add_remark)==0:
                add_remark=None
            if check_type=="true":
                models.UserTable.objects.create(user_code=add_user_code, user_password="123456",dpartment_name_id=login_dpartment_name_id,
                                                user_name=add_user_name,user_mail=add_user_mail,user_phone=add_user_phone,user_stat="1",
                                                user_type="1",stu_num=add_stu_num,remark=add_remark,op_no=login_user_code)
            else:
                models.UserTable.objects.create(user_code=add_user_code, user_password="123456",dpartment_name_id=login_dpartment_name_id,
                                                user_name=add_user_name,user_mail=add_user_mail,user_phone=add_user_phone,user_stat="1",
                                                user_type="0",stu_num=None,remark=add_remark,op_no=login_user_code)
            dic_user_list = []
            obj = models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),dpartment_name_id=login_dpartment_name_id)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        elif operate=="change":
            change_user_code=request.POST.get('change_user_code', None)   #获取操作的账号
            change_user_name=request.POST.get('change_user_name', None)   #用户名
            change_user_password=request.POST.get('change_user_password', None)
            change_stu_num=request.POST.get('change_stu_num', None)        #指导学生数量 空字符串代表学生   非空字符串代表老师
            change_user_mail=request.POST.get('change_user_mail', None)
            change_user_phone=request.POST.get('change_user_phone', None)
            change_remark=request.POST.get('change_remark', None)
            check_password=request.POST.get('check_password', None)

            obj = models.UserTable.objects.filter(user_code=change_user_code).first()  #查找用户相关信息
            up_data_dic = {'user_name': obj.user_name,
                           'user_password': obj.user_password,
                           'user_mail': obj.user_mail,
                           'user_phone': obj.user_phone,
                           'stu_num': obj.stu_num,
                           'remark': obj.remark,
                           "op_no": login_user_code
                           }
            if change_user_name=="":
                return_data['status'] = False
                return_data['data'] = "姓名不能不空"
                return JsonResponse(return_data, safe=False)
            up_data_dic['user_name']=change_user_name
            if check_password=="true":
                if change_user_password=="":
                    return_data['status'] = False
                    return_data['data'] = "密码不能不空"
                    return JsonResponse(return_data, safe=False)
                up_data_dic['user_password'] = change_user_password
            if change_user_mail == "无" or change_user_mail == "":
                up_data_dic["user_mail"] = None
            else:
                up_data_dic["user_mail"] = change_user_mail
            if change_user_phone == "无" or change_user_phone == "":
                up_data_dic["user_phone"] = None
            else:
                up_data_dic["user_phone"] = change_user_phone
            if change_remark == "无" or change_remark == "":
                up_data_dic["remark"] = None
            else:
                up_data_dic["remark"] =change_remark

            if change_stu_num=="" and obj.user_type=="1":
                return_data['status'] = False
                return_data['data'] = "指导学生数量不能为空"
                return JsonResponse(return_data, safe=False)
            if change_stu_num=="":
                up_data_dic["stu_num"] = None
            else:
                up_data_dic["stu_num"] =change_stu_num

            models.UserTable.objects.filter(user_code=change_user_code).update(user_name=up_data_dic["user_name"],
                                                                        user_password=up_data_dic["user_password"],
                                                                        user_mail=up_data_dic["user_mail"],
                                                                        stu_num=up_data_dic["stu_num"],
                                                                        user_phone=up_data_dic["user_phone"],
                                                                        remark=up_data_dic["remark"],
                                                                        op_no=up_data_dic["op_no"])
            dic_user_list = []
            obj = models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),dpartment_name_id=login_dpartment_name_id)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        elif operate=="freeze":
            freeze_user_code=request.POST.get('freeze_user_code', None)   #获取冻结的账号
            models.UserTable.objects.filter(user_code=freeze_user_code).update(user_stat="2")               #操作的账号冻结
            dic_user_list = []
            obj = models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),dpartment_name_id=login_dpartment_name_id)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        elif operate=="unfreeze":
            unfreeze_user_code=request.POST.get('unfreeze_user_code', None)   #获解冻的账号
            models.UserTable.objects.filter(user_code=unfreeze_user_code).update(user_stat="1")
            dic_user_list = []
            obj = models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),dpartment_name_id=login_dpartment_name_id)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        # 删除时直接删掉 当前的用户
        elif operate=="delete":
            delete_user_code=request.POST.get('delete_user_code', None)   #获取删除的账号
            models.UserTable.objects.filter(user_code=delete_user_code).first().delete()
            dic_user_list = []
            obj = models.UserTable.objects.filter(Q(user_type=1) | Q(user_type=0),dpartment_name_id=login_dpartment_name_id)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        else:
            return_data['status'] = False
            return_data['data'] = "未知错误"
            return JsonResponse(return_data, safe=False)         #前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
    else:
        return HttpResponse("该页面还在准备中@@")


def check(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '2':
            return render(request, 'DirCheck.html')
        else:
            return render(request, 'login.html')

    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取系主任的账号
        login_dpartment_name_id=models.UserTable.objects.filter(user_code=login_user_code).first().dpartment_name_id  #获取系主任所属的系号
        return_data = {'status': True, 'data': None}   #返回的数据初始化
        operate = request.POST.get('operate', None)  # 获取需要的操作
        if operate=="search":
            find_user_name=request.POST.get('find_user_name', None)           #用户名
            find_year=request.POST.get('find_year', None)                   #查找年级
            select_postil_flag=request.POST.get('select_postil_flag', None)     #选择类型 0未审核 1已通过 2未通过 3全部
            dic_user_list=[]                                            #找到数据后返回的列表
            obj = []
            if find_user_name=="":
                if find_year=="":
                    if select_postil_flag == "3":
                        obj = models.SubjectTable.objects.filter(dpartment_name_id=login_dpartment_name_id)  #查找所有该系老师的选题信息
                    else:
                        obj = models.SubjectTable.objects.filter(postil_flag=select_postil_flag,dpartment_name_id=login_dpartment_name_id)
                else:
                    if select_postil_flag == "3":
                        obj = models.SubjectTable.objects.filter(year=find_year,dpartment_name_id=login_dpartment_name_id)
                    else:
                        obj = models.SubjectTable.objects.filter(year=find_year,postil_flag=select_postil_flag,dpartment_name_id=login_dpartment_name_id)
            else:
                if len(models.UserTable.objects.filter(user_name=find_user_name)) > 0:
                    user_code=models.UserTable.objects.filter(user_name=find_user_name).first().user_code       #获取老师名字 从数据库转换成用户ID
                    # 根据老师的姓名
                    if find_year == "":
                        if select_postil_flag == "3":
                            obj = models.SubjectTable.objects.filter(teacher_no=user_code,dpartment_name_id=login_dpartment_name_id)
                        else:
                            obj = models.SubjectTable.objects.filter(teacher_no=user_code, postil_flag = select_postil_flag, dpartment_name_id = login_dpartment_name_id)
                    else:
                        if select_postil_flag == "3":
                            obj = models.SubjectTable.objects.filter(teacher_no=user_code, year = find_year, dpartment_name_id = login_dpartment_name_id)
                        else:
                            obj = models.SubjectTable.objects.filter(teacher_no=user_code, year = find_year, postil_flag = select_postil_flag, dpartment_name_id = login_dpartment_name_id)
            if len(obj)==0:
                return_data['status']=False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)       #对象数据转字典
                    user_name=models.UserTable.objects.filter(user_code=jsonstr['teacher_no']).first().user_name
                    jsonstr['user_name']= user_name          #在字典里增加 老师的名字
                    dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象

        elif operate=="check":
            check_sub_id=request.POST.get('check_sub_id', None)             #获取操作的题号
            check_postil_flag=request.POST.get('check_postil_flag', None)   #审核情况  1表示通过   2表示不通过
            check_postil=request.POST.get('check_postil', None)              #审核意见和建议

            obj = models.SubjectTable.objects.filter(id=check_sub_id).first()  #查找题目信息
            up_data_dic = {'postil_flag': obj.postil_flag,
                           'postil': obj.postil,
                           "op_no": login_user_code
                           }
            if check_postil=="":
                return_data['status'] = False
                return_data['data'] = "审核意见不能为空"
                return JsonResponse(return_data, safe=False)
            up_data_dic['postil']=check_postil
            up_data_dic['postil_flag']=check_postil_flag
            models.SubjectTable.objects.filter(id=check_sub_id).update(postil_flag=up_data_dic["postil_flag"],
                                                                       postil=up_data_dic["postil"],
                                                                        op_no=up_data_dic["op_no"])
            dic_user_list = []
            obj = models.SubjectTable.objects.filter(dpartment_name_id=login_dpartment_name_id)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                user_name=models.UserTable.objects.filter(user_code=jsonstr['teacher_no']).first().user_name
                jsonstr['user_name']= user_name          #在字典里增加 老师的名字
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
        else:
            return_data['status'] = False
            return_data['data'] = "未知错误"
            return JsonResponse(return_data, safe=False)         #前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
    else:
        return HttpResponse("该页面还在准备中@@")



def history(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '2':
            return render(request, 'DirHistory.html')
        else:
            return render(request, 'login.html')

    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取系主任的账号
        login_dpartment_name_id=models.UserTable.objects.filter(user_code=login_user_code).first().dpartment_name_id  #获取系主任所属的系号
        return_data = {'status': True, 'data': None}   #返回的数据初始化
        operate = request.POST.get('operate', None)  # 获取需要的操作
        if operate=="search":
            find_user_name=request.POST.get('find_user_name', None)           #用户名
            find_year=request.POST.get('find_year', None)                   #查找年级
            dic_user_list=[]                                            #找到数据后返回的列表
            obj = []
            if find_user_name=="":
                if find_year=="":
                    obj = models.SubjectTable.objects.filter(postil_flag="1",dpartment_name_id=login_dpartment_name_id)
                else:
                    obj = models.SubjectTable.objects.filter(year=find_year,postil_flag="1",dpartment_name_id=login_dpartment_name_id)
            else:
                if len(models.UserTable.objects.filter(user_name=find_user_name)) > 0:       #检查导师是否存在
                    user_code=models.UserTable.objects.filter(user_name=find_user_name).first().user_code       #获取老师名字 从数据库转换成用户ID
                    # 根据老师的姓名
                    if find_year == "":
                        obj = models.SubjectTable.objects.filter(teacher_no=user_code, postil_flag = "1", dpartment_name_id = login_dpartment_name_id)
                    else:
                        obj = models.SubjectTable.objects.filter(teacher_no=user_code, year = find_year, postil_flag = "1", dpartment_name_id = login_dpartment_name_id)
            if len(obj)==0:
                return_data['status']=False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)       #对象数据转字典
                    user_name=models.UserTable.objects.filter(user_code=jsonstr['teacher_no']).first().user_name
                    jsonstr['user_name']= user_name          #在字典里增加 老师的名字
                    jsonstr['check_wish'] = len(models.SelectSubTable.objects.filter(sub_no=line.id, postil_flag="1"))   #通过审核的人数
                    jsonstr['wish_flag1'] = len(models.SelectSubTable.objects.filter(sub_no=line.id,wish_flag='1'))    #找到该题目 选择为第一志愿的人数
                    jsonstr['wish_flag2'] = len(models.SelectSubTable.objects.filter(sub_no=line.id,wish_flag='2'))    #找到该题目 选择为第二志愿的人数
                    jsonstr['wish_flag3'] = len(models.SelectSubTable.objects.filter(sub_no=line.id,wish_flag='3'))    #找到该题目 选择为第三志愿的人数
                    jsonstr['wish_flag4'] = len(models.SelectSubTable.objects.filter(sub_no=line.id,wish_flag='4'))    #找到该题目 选择为第四志愿的人数
                    dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
        else:
            return_data['status'] = False
            return_data['data'] = "未知错误"
            return JsonResponse(return_data, safe=False)         #前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
    else:
        return HttpResponse("该页面还在准备中@@")


def person(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '2':
            #登录成功后的操作
            user_code=request.session['user_code']   #获取操操作户账号
            obj = models.UserTable.objects.filter(user_code=user_code).first()  #查找用户相关信息
            return_dic={'user_code':obj.user_code,
                        'user_name': obj.user_name,
                        'dpartment_name':obj.dpartment_name.dpartement_name,
                        'user_mail': obj.user_mail,
                        'user_phone': obj.user_phone,
                        'remark': obj.remark
            }
            return_dic['user_mail']='无' if obj.user_mail is None else obj.user_mail
            return_dic['user_phone']='无' if obj.user_phone is None else obj.user_phone
            return_dic['remark']='无' if obj.remark is None else obj.remark
            return render(request,'DirPerson.html',return_dic)
        else:
            return render(request, 'login.html')
    elif request.method == "POST":
        ret = {'status': True, 'error': None}
        user_code = request.session['user_code']  # 获取操作用户账号
        obj = models.UserTable.objects.filter(user_code=user_code).first()
        up_data_dic = {'user_name': obj.user_name,
                       'user_password': obj.user_password,
                      'user_mail': obj.user_mail,
                      'user_phone': obj.user_phone,
                       "op_no":user_code
                      }

        user_name = request.POST.get('user_name', None)  # 沒有则为空
        old_password = request.POST.get('old_password', None)
        new_password = request.POST.get('new_password', None)
        again_password = request.POST.get('again_password', None)
        user_phone = request.POST.get('user_phone', None)
        user_mail = request.POST.get('user_mail', None)
        change_password = request.POST.get('change_password', None)

        if len(user_name)==0:
            ret['status'] = False
            ret['error'] = '姓名不能为空'
            return HttpResponse(json.dumps(ret))
        up_data_dic["user_name"] = user_name

        if change_password == "true":
            if old_password == obj.user_password:
                if new_password!=again_password:
                    ret['status'] = False
                    ret['error'] = '两次密码输入不一致'
                    return HttpResponse(json.dumps(ret))
            else:
                ret['status'] = False
                ret['error'] = '原始密码错误'
                return HttpResponse(json.dumps(ret))
            up_data_dic["user_password"]=new_password

        if  user_phone== "无" or user_phone== "":
            up_data_dic["user_phone"] = None
        else:
            up_data_dic["user_phone"] = user_phone
        if  user_mail== "无" or user_mail== "":
            up_data_dic["user_mail"] = None
        else:
            up_data_dic["user_mail"] = user_mail

        models.UserTable.objects.filter(user_code=user_code).update(user_name=up_data_dic["user_name"],user_mail=up_data_dic["user_mail"],
                                                                    user_phone=up_data_dic["user_phone"],user_password=up_data_dic["user_password"],
                                                                    op_no=up_data_dic["op_no"])
        return HttpResponse(json.dumps(ret))


def logout(request):
    # del request.session['user_code']
    request.session.clear()
    return redirect('/login/')

