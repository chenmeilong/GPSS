#managerr APP

from django.shortcuts import render
from django.shortcuts import render,HttpResponse,redirect
import json
from manager import models
from django.http import JsonResponse
from django.forms.models import model_to_dict
def login(request):
    if request.method == "GET":
        return render(request, 'login.html')
    elif request.method == "POST":
        ret = {'status': True, 'error': None}
        try:
            user_code = request.POST.get('man_username',None)    #沒有则为空
            password = request.POST.get('man_password',None)
            remember = request.POST.get('man_remember',None)   #这是Ture 记住密码or falase不记住
            #print("记住密码:", remember)
            obj = models.UserTable.objects.filter(user_code=user_code,user_type='3').first()  #找到用户  且用户为管理员
            if obj:
                print("用户存在")
                if obj.user_password==password:
                    request.session['is_login'] = True
                    request.session['user_code'] = user_code
                    request.session['user_type'] ='3'             #在session写入用户的类型  给与不同用户不同的权限
                    request.session.set_expiry(24*60*60)  #一天免登陆
                    if remember=="True":
                        request.session.set_expiry(14*24*60*60)    # 两周免登陆
                else:
                    ret['status'] = False
                    ret['error'] = "密码错误请重新输入"
            else:
                ret['status'] = False
                ret['error'] = "管理员号不存在请重新输入"
        except Exception as e:
            ret['status'] = False
            ret['error'] = '未知错误'
        return HttpResponse(json.dumps(ret))
    else:
        return HttpResponse("该页面还在准备中@@")


def home(request):
    if request.method == "GET":
        # session中获取值
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '3':
            #登录成功后的操作
            user_code=request.session['user_code']   #用户账号
            obj = models.UserTable.objects.filter(user_code=user_code).first()  #查找用户相关信息
            return render(request,'ManHome.html',{'user_name':obj.user_name})
        else:
            return render(request, 'login.html')
    else:
        return HttpResponse("该页面还在准备中@@")


def manage(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '3':
            return render(request, 'ManManage.html')
        else:
            return render(request, 'login.html')
    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取操操作户账号
        return_data = {'status': True, 'data': None}
        operate = request.POST.get('operate', None)  # 获取需要的操作
        if operate=="search":
            find_user_name=request.POST.get('find_user_name', None)   #用户名
            select_stat=request.POST.get('select_stat', None)         #0表示全部  1表示正常 2冻结
            dic_user_list=[]
            if find_user_name=="":
                if select_stat=="0":
                    obj = models.UserTable.objects.filter(user_type=2)
                else:
                    obj = models.UserTable.objects.filter(user_stat=select_stat,user_type=2)
            elif select_stat=="0":
                obj = models.UserTable.objects.filter(user_name=find_user_name,user_type=2)
            else:
                obj = models.UserTable.objects.filter(user_name=find_user_name,user_stat= select_stat,user_type=2)
            if len(obj)==0:
                return_data['status']=False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)       #对象数据转字典
                    jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                    dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象

        elif operate=="add":
            add_user_name=request.POST.get('add_user_name', None)   #用户名
            add_user_code=request.POST.get('add_user_code', None)    #账号
            add_user_mail=request.POST.get('add_user_mail', None)
            add_department_name=request.POST.get('add_department_name', None) #系名
            add_user_phone=request.POST.get('add_user_phone', None)
            add_remark=request.POST.get('add_remark', None)
            if add_user_name=="":
                return_data['status'] = False
                return_data['data'] = "姓名不能不空"
                return JsonResponse(return_data, safe=False)
            if add_user_code=="":
                return_data['status'] = False
                return_data['data'] = "登录账号不能不空"
                return JsonResponse(return_data, safe=False)
            if add_department_name=="":
                return_data['status'] = False
                return_data['data'] = "系名不能不空"
                return JsonResponse(return_data, safe=False)
            if len(models.UserTable.objects.filter(user_code=add_user_code, user_type=2))>0:
                return_data['status'] = False
                return_data['data'] = "该登录账号已存在"
                return JsonResponse(return_data, safe=False)

            if len(models.DpartmentTable.objects.filter(dpartement_name=add_department_name)) > 0:        #系表中查看系是否存在
                return_data['status'] = False
                return_data['data'] = "系名已存在"
                return JsonResponse(return_data, safe=False)
            models.DpartmentTable.objects.create(dpartement_name=add_department_name)   #创建系
            dpartment_name_id=models.DpartmentTable.objects.filter(dpartement_name=add_department_name).first().id
            if len(add_user_mail)==0:
                add_user_mail=None
            if len(add_user_phone)==0:
                add_user_phone=None
            if len(add_remark)==0:
                add_remark=None

            models.UserTable.objects.create(user_code=add_user_code, user_password="123456",dpartment_name_id=dpartment_name_id,
                                            user_name=add_user_name,user_mail=add_user_mail,user_phone=add_user_phone,user_stat="1",
                                            user_type="2",stu_num=None,remark=add_remark,op_no=login_user_code)
            dic_user_list = []
            obj = models.UserTable.objects.filter(user_type=2)
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
            change_department_name=request.POST.get('change_department_name', None) #系名真实的名字
            change_user_mail=request.POST.get('change_user_mail', None)
            change_user_phone=request.POST.get('change_user_phone', None)
            change_remark=request.POST.get('change_remark', None)
            check_password=request.POST.get('check_password', None)

            obj = models.UserTable.objects.filter(user_code=change_user_code).first()  #查找用户相关信息
            up_data_dic = {'user_name': obj.user_name,
                           'user_password': obj.user_password,
                           'user_mail': obj.user_mail,
                           'user_phone': obj.user_phone,
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

            if change_department_name=="":
                return_data['status'] = False
                return_data['data'] = "系名不能不空"
                return JsonResponse(return_data, safe=False)
            if len(models.DpartmentTable.objects.filter(dpartement_name=change_department_name)) ==0:
                models.DpartmentTable.objects.filter(id=obj.dpartment_name_id).update(dpartement_name=change_department_name)   #更新数据库的系名
            elif models.DpartmentTable.objects.filter(dpartement_name=change_department_name).first().id!=obj.dpartment_name_id:
                return_data['status'] = False
                return_data['data'] = "该系已存在"
                return JsonResponse(return_data, safe=False)
            models.UserTable.objects.filter(user_code=change_user_code).update(user_name=up_data_dic["user_name"],
                                                                        user_password=up_data_dic["user_password"],
                                                                        user_mail=up_data_dic["user_mail"],
                                                                        user_phone=up_data_dic["user_phone"],
                                                                        remark=up_data_dic["remark"],
                                                                        op_no=up_data_dic["op_no"])
            dic_user_list = []
            obj = models.UserTable.objects.filter(user_type=2)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        elif operate=="freeze":
            freeze_user_code=request.POST.get('freeze_user_code', None)   #获取冻结的账号
            dpartment_name_id=models.UserTable.objects.filter(user_code=freeze_user_code).first().dpartment_name_id
            models.UserTable.objects.filter(dpartment_name_id=dpartment_name_id).update(user_stat="2")               #批量冻结 对系里的所有老师和学生冻结
            dic_user_list = []
            obj = models.UserTable.objects.filter(user_type=2)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        elif operate=="unfreeze":
            unfreeze_user_code=request.POST.get('unfreeze_user_code', None)   #获解冻的账号
            dpartment_name_id=models.UserTable.objects.filter(user_code=unfreeze_user_code).first().dpartment_name_id
            models.UserTable.objects.filter(dpartment_name_id=dpartment_name_id).update(user_stat="1")

            dic_user_list = []
            obj = models.UserTable.objects.filter(user_type=2)
            for line in obj:
                jsonstr = model_to_dict(line)       #对象数据转字典
                jsonstr['dpartment_name']=line.dpartment_name.dpartement_name         #更改系的数据 外键操作
                dic_user_list.append(jsonstr)
            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        # 删除时删掉系名 即可删除相关联 用户表 的所有数据
        elif operate=="delete":
            delete_user_code=request.POST.get('delete_user_code', None)   #获取删除的账号
            models.DpartmentTable.objects.filter(id=models.UserTable.objects.filter(user_code=delete_user_code).first().dpartment_name_id).delete()
            dic_user_list = []
            obj = models.UserTable.objects.filter(user_type=2)
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


def person(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '3':
            #登录成功后的操作
            user_code=request.session['user_code']   #获取操操作户账号
            obj = models.UserTable.objects.filter(user_code=user_code).first()  #查找用户相关信息
            return_dic={'user_code':obj.user_code,
                        'user_name': obj.user_name,
                        'user_mail': obj.user_mail,
                        'user_phone': obj.user_phone,
                        'remark': obj.remark
            }
            return_dic['user_mail']='无' if obj.user_mail is None else obj.user_mail
            return_dic['user_phone']='无' if obj.user_phone is None else obj.user_phone
            return_dic['remark']='无' if obj.remark is None else obj.remark
            return render(request,'ManPerson.html',return_dic)
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

