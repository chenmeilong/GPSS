#teacher APP

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
            user_code = request.POST.get('tea_username',None)    #沒有则为空
            password = request.POST.get('tea_password',None)
            remember = request.POST.get('tea_remember',None)   #这是Ture 记住密码or falase不记住
            obj = models.UserTable.objects.filter(user_code=user_code,user_type='1').first()  #找到用户  且用户为老师
            print(obj)
            if obj:
                if obj.user_stat=="1":
                    if obj.user_password==password:
                        request.session['is_login'] = True
                        request.session['user_code'] = user_code
                        request.session['user_type'] ='1'             #在session写入用户的类型  给与不同用户不同的权限
                        request.session.set_expiry(24*60*60)  #一天免登陆
                        if remember=="True":
                            request.session.set_expiry(14*24*60*60)    # 两周内免登陆
                            print("设置了一小时免登陆")
                    else:
                        ret['status'] = False
                        ret['error'] = "密码错误请重新输入"
                else:
                    ret['status'] = False
                    ret['error'] = "该账号已冻结请联系系主任"
            else:
                ret['status'] = False
                ret['error'] = "教工号不存在请联系系主任注册"
        except Exception as e:
            ret['status'] = False
            ret['error'] = '未知错误'
        return HttpResponse(json.dumps(ret))
    else:
        return HttpResponse("该页面还在准备中@@")

def home(request):
    if request.method == "GET":
        # session中获取值
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '1':
            #登录成功后的操作
            user_code=request.session['user_code']   #用户账号
            obj = models.UserTable.objects.filter(user_code=user_code).first()  #查找用户相关信息
            return render(request,'TeaHome.html',{'user_name':obj.user_name})
        else:
            return render(request, 'login.html')
    else:
        return HttpResponse("该页面还在准备中@@")


def propose(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '1':
            return render(request, 'TeaPropose.html')
        else:
            return render(request, 'login.html')

    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取导师的账号
        login_dpartment_name_id=models.UserTable.objects.filter(user_code=login_user_code).first().dpartment_name_id  #获取导师所属的系号
        return_data = {'status': True, 'data': None}   #返回的数据初始化
        operate = request.POST.get('operate', None)  # 获取需要的操作
        if operate=="search":
            find_year = request.POST.get('find_year', None)  # 查找年级
            select_postil_flag = request.POST.get('select_postil_flag', None)  # 选择类型 0未审核 1已通过 2未通过 3全部
            dic_user_list = []  # 找到数据后返回的列表
            obj = []
            if find_year == "":
                if select_postil_flag == "3":
                    obj = models.SubjectTable.objects.filter(teacher_no=login_user_code,
                                                             dpartment_name_id=login_dpartment_name_id)
                else:
                    obj = models.SubjectTable.objects.filter(teacher_no=login_user_code,
                                                             postil_flag=select_postil_flag,
                                                             dpartment_name_id=login_dpartment_name_id)
            else:
                if select_postil_flag == "3":
                    obj = models.SubjectTable.objects.filter(teacher_no=login_user_code, year=find_year,
                                                             dpartment_name_id=login_dpartment_name_id)
                else:
                    obj = models.SubjectTable.objects.filter(teacher_no=login_user_code, year=find_year,
                                                             postil_flag=select_postil_flag,
                                                             dpartment_name_id=login_dpartment_name_id)
            if len(obj) == 0:
                return_data['status'] = False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)  # 对象数据转字典
                    dic_user_list.append(jsonstr)
            return_data['data'] = dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象

        elif operate=="add":
            add_sub_name=request.POST.get('add_sub_name', None)   #论文题目
            add_year=request.POST.get('add_year', None)           #参与年级
            add_part_in_no=request.POST.get('add_part_in_no', None)    #限制参与人数
            add_sub_viscera=request.POST.get('add_sub_viscera', None)        #详细题目
            if add_sub_name=="":
                return_data['status'] = False
                return_data['data'] = "论文题目不能不空"
                return JsonResponse(return_data, safe=False)
            if add_year=="":
                return_data['status'] = False
                return_data['data'] = "年级不能为空"
                return JsonResponse(return_data, safe=False)
            if add_sub_viscera=="":
                return_data['status'] = False
                return_data['data'] = "题目内容不能为空"
                return JsonResponse(return_data, safe=False)
            if add_part_in_no == "":
                return_data['status'] = False
                return_data['data'] = "参与人数不能为空"
                return JsonResponse(return_data, safe=False)
            else:
                # 判断人数上限
                max_stu_num=models.UserTable.objects.filter(user_code=login_user_code).first().stu_num  # 获取导师最大指导人数上限
                stu_num=int(add_part_in_no)
                obj = models.SubjectTable.objects.filter(teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                for line in obj:
                    stu_num=stu_num+int(line.part_in_no)
                if stu_num>int(max_stu_num):
                    return_data['status'] = False
                    return_data['data'] = "论文参与人数和不能超过最大指导人数"
                    return JsonResponse(return_data, safe=False)
            #增加论文题目
            models.SubjectTable.objects.create(sub_name=add_sub_name,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id,
                                               part_in_no=add_part_in_no,sub_viscera=add_sub_viscera,postil_flag="0",year=add_year,op_no=login_user_code)

            dic_user_list = []
            obj = models.SubjectTable.objects.filter(teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)    #查找该老师的所有题目返回
            for line in obj:
                jsonstr = model_to_dict(line)  # 对象数据转字典
                dic_user_list.append(jsonstr)
            return_data['data'] = dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象

        elif operate=="change":
            change_sub_id=request.POST.get('change_sub_id', None)              #获取操作的题号
            change_sub_name=request.POST.get('change_sub_name', None)          #论文题目
            change_year=request.POST.get('change_year', None)                  #年级
            change_part_in_no=request.POST.get('change_part_in_no', None)      #参与人数上限
            change_sub_viscera=request.POST.get('change_sub_viscera', None)    #题目详情

            if change_sub_name=="":
                return_data['status'] = False
                return_data['data'] = "论文题目不能不空"
                return JsonResponse(return_data, safe=False)
            if change_year=="":
                return_data['status'] = False
                return_data['data'] = "年级不能为空"
                return JsonResponse(return_data, safe=False)
            if change_sub_viscera=="":
                return_data['status'] = False
                return_data['data'] = "题目内容不能为空"
                return JsonResponse(return_data, safe=False)
            if change_part_in_no == "":
                return_data['status'] = False
                return_data['data'] = "参与人数不能为空"
                return JsonResponse(return_data, safe=False)
            else:
                # 判断人数上限
                max_stu_num=models.UserTable.objects.filter(user_code=login_user_code).first().stu_num  # 获取导师最大指导人数上限
                stu_num=int(change_part_in_no)
                obj = models.SubjectTable.objects.filter(teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                for line in obj:
                    if line.id!=int(change_sub_id):
                        stu_num=stu_num+int(line.part_in_no)
                if stu_num>int(max_stu_num):
                    return_data['status'] = False
                    return_data['data'] = "论文参与人数和不能超过最大指导人数"
                    return JsonResponse(return_data, safe=False)

            models.SubjectTable.objects.filter(id=change_sub_id).update(sub_name=change_sub_name,
                                                                        year=change_year,
                                                                        part_in_no=change_part_in_no,
                                                                        sub_viscera=change_sub_viscera,
                                                                        postil_flag="0",
                                                                        op_no=login_user_code)           #修改后设置为未审核
            dic_user_list = []
            obj = models.SubjectTable.objects.filter(teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)    #查找该老师的所有题目返回
            for line in obj:
                jsonstr = model_to_dict(line)  # 对象数据转字典
                dic_user_list.append(jsonstr)
            return_data['data'] = dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象

        # 删除时直接删掉 当前的用户
        elif operate=="delete":
            delete_sub_id=request.POST.get('delete_sub_id', None)   #获取删除的题号
            models.SubjectTable.objects.filter(id=delete_sub_id).first().delete()
            dic_user_list = []
            obj = models.SubjectTable.objects.filter(teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)    #查找该老师的所有题目返回
            for line in obj:
                jsonstr = model_to_dict(line)  # 对象数据转字典
                dic_user_list.append(jsonstr)
            return_data['data'] = dic_user_list
            return JsonResponse(return_data, safe=False)  # 前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象

        else:
            return_data['status'] = False
            return_data['data'] = "未知错误"
            return JsonResponse(return_data, safe=False)         #前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
    else:
        return HttpResponse("该页面还在准备中@@")


def check(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '1':
            return render(request, 'TeaCheck.html')
        else:
            return render(request, 'login.html')

    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取登录老师的账号
        login_dpartment_name_id=models.UserTable.objects.filter(user_code=login_user_code).first().dpartment_name_id  #获取登录老师所属的系号
        return_data = {'status': True, 'data': None}   #返回的数据初始化
        operate = request.POST.get('operate', None)  # 获取需要的操作

        #  find_sub_name     find_year   select_wish_flag  select_postil_flag
        if operate=="search":
            find_sub_name=request.POST.get('find_sub_name', None)           #论文名称
            find_year=request.POST.get('find_year', None)                   #查找年级
            select_wish_flag=request.POST.get('select_wish_flag', None)     #选择的意愿  0 全部 1第一志愿 2第二志愿 3第三志愿 4第四志愿
            select_postil_flag=request.POST.get('select_postil_flag', None)     #选择类型 0未审核 1已通过 2未通过 3全部

            obj = []
            if find_sub_name=="":
                if find_year=="":
                    if select_wish_flag=='0':
                        if select_postil_flag == "3":
                            obj = models.SelectSubTable.objects.filter(Q(postil_flag="0")|Q(postil_flag="1"),teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)  #查找所有该老师的学生选题信息
                        else:
                            obj = models.SelectSubTable.objects.filter(postil_flag=select_postil_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                    else:
                        if select_postil_flag == "3":
                            obj = models.SelectSubTable.objects.filter(Q(postil_flag="0")|Q(postil_flag="1"),wish_flag=select_wish_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                        else:
                            obj = models.SelectSubTable.objects.filter(wish_flag=select_wish_flag,postil_flag=select_postil_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)

                else:
                    if select_wish_flag == '0':
                        if select_postil_flag == "3":
                            obj = models.SelectSubTable.objects.filter(Q(postil_flag="0")|Q(postil_flag="1"),year=find_year,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                        else:
                            obj = models.SelectSubTable.objects.filter(year=find_year,postil_flag=select_postil_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                    else:
                        if select_postil_flag == "3":
                            obj = models.SelectSubTable.objects.filter(Q(postil_flag="0")|Q(postil_flag="1"),year=find_year,wish_flag=select_wish_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                        else:
                            obj = models.SelectSubTable.objects.filter(year=find_year,wish_flag=select_wish_flag,postil_flag=select_postil_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)

            else:
                if len(models.SubjectTable.objects.filter(sub_name=find_sub_name)) > 0:
                    sub_no=models.SubjectTable.objects.filter(sub_name=find_sub_name).first().id       #获論文取名字的id 从数据库转换成論文ID
                    if find_year == "":
                        if select_wish_flag == '0':
                            if select_postil_flag == "3":
                                obj = models.SelectSubTable.objects.filter(Q(postil_flag="0")|Q(postil_flag="1"),sub_no=sub_no,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)  # 查找所有该系老师的学生选题信息 已审核和未审核的
                            else:
                                obj = models.SelectSubTable.objects.filter(sub_no=sub_no,postil_flag=select_postil_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                        else:
                            if select_postil_flag == "3":
                                obj = models.SelectSubTable.objects.filter(Q(postil_flag="0")|Q(postil_flag="1"),sub_no=sub_no,wish_flag=select_wish_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                            else:
                                obj = models.SelectSubTable.objects.filter(sub_no=sub_no,wish_flag=select_wish_flag,postil_flag=select_postil_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)

                    else:
                        if select_wish_flag == '0':
                            if select_postil_flag == "3":
                                obj = models.SelectSubTable.objects.filter(Q(postil_flag="0")|Q(postil_flag="1"),sub_no=sub_no,year=find_year, teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                            else:
                                obj = models.SelectSubTable.objects.filter(sub_no=sub_no,year=find_year,postil_flag=select_postil_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                        else:
                            if select_postil_flag == "3":
                                obj = models.SelectSubTable.objects.filter(Q(postil_flag="0")|Q(postil_flag="1"),sub_no=sub_no,year=find_year, wish_flag=select_wish_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
                            else:
                                obj = models.SelectSubTable.objects.filter(sub_no=sub_no,year=find_year, wish_flag=select_wish_flag,postil_flag=select_postil_flag,teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)

            dic_user_list=[]                                            #找到数据后返回的列表
            if len(obj)==0:
                return_data['status']=False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)       #对象数据转字典
                    #按照志愿顺序 和审核情况选择是否要显回传前端数据
                    stu_select_order = models.SelectSubTable.objects.filter(stu_no=jsonstr['stu_no']).order_by("wish_flag")    # 正常学生有四个志愿 按照 1234志愿排序
                    for wish in stu_select_order:
                        if wish.postil_flag=="0" or wish.postil_flag=="1":   #  0未审核  1审核通过   2不通过
                            if wish.id==line.id:
                                user_name = models.UserTable.objects.filter(user_code=jsonstr['stu_no']).first().user_name
                                jsonstr['user_name'] = user_name  # 在字典里增加 學生的名字
                                sub_name = models.SubjectTable.objects.filter(id=jsonstr['sub_no']).first().sub_name
                                jsonstr['sub_name'] = sub_name  # 在字典里增加 論文的題目
                                dic_user_list.append(jsonstr)
                            break

            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        elif operate=="check":
            check_select_id=request.POST.get('check_select_id', None)             #获取操作的 选择id号
            check_postil_flag=request.POST.get('check_postil_flag', None)   #审核情况  1表示通过   2表示不通过
            check_postil=request.POST.get('check_postil', None)              #审核意见和建议

            obj = models.SelectSubTable.objects.filter(id=check_select_id).first()  #查找 选择题目的 信息
            up_data_dic = {'postil_flag': obj.postil_flag,
                           'postil': obj.postil,
                           "op_no": login_user_code
                           }
            if check_postil=="":
                return_data['status'] = False
                return_data['data'] = "审核意见不能为空"
                return JsonResponse(return_data, safe=False)


            max_part_in_no=models.SubjectTable.objects.filter(id=obj.sub_no).first().part_in_no   #参与人数上限
            if len(models.SelectSubTable.objects.filter(sub_no=obj.sub_no,postil_flag="1"))>= int(max_part_in_no) and check_postil_flag=="1":
                return_data['status'] = False
                return_data['data'] = "参与人数已达上限"
                return JsonResponse(return_data, safe=False)    #所有通过审核  的选题人数 大于等于 最大参与人数 则不能审核成功

            up_data_dic['postil']=check_postil
            up_data_dic['postil_flag']=check_postil_flag
            models.SelectSubTable.objects.filter(id=check_select_id).update(postil_flag=up_data_dic["postil_flag"],
                                                                       postil=up_data_dic["postil"],
                                                                        op_no=up_data_dic["op_no"])

            obj = models.SelectSubTable.objects.filter(Q(postil_flag="0") | Q(postil_flag="1"),teacher_no=login_user_code,dpartment_name_id=login_dpartment_name_id)
            dic_user_list=[]                                            #找到数据后返回的列表
            if len(obj)==0:
                return_data['status']=False
            else:
                for line in obj:
                    jsonstr = model_to_dict(line)       #对象数据转字典
                    #按照志愿顺序 和审核情况选择是否要显回传前端数据
                    stu_select_order = models.SelectSubTable.objects.filter(stu_no=jsonstr['stu_no']).order_by("wish_flag")    # 正常学生有四个志愿 按照 1234志愿排序
                    for wish in stu_select_order:
                        if wish.postil_flag=="0" or wish.postil_flag=="1":   #  0未审核  1审核通过   2不通过
                            if wish.id==line.id:
                                user_name = models.UserTable.objects.filter(user_code=jsonstr['stu_no']).first().user_name
                                jsonstr['user_name'] = user_name  # 在字典里增加 學生的名字
                                sub_name = models.SubjectTable.objects.filter(id=jsonstr['sub_no']).first().sub_name
                                jsonstr['sub_name'] = sub_name  # 在字典里增加 論文的題目
                                dic_user_list.append(jsonstr)
                            break

            return_data['data'] =  dic_user_list
            return JsonResponse(return_data, safe=False)

        else:
            return_data['status'] = False
            return_data['data'] = "未知错误"
            return JsonResponse(return_data, safe=False)         #前端后端  都不需要序列号 和反序列化操作 return_data可以为字典列表元组 不可以为对象
    else:
        return HttpResponse("该页面还在准备中@@")




def history(request):
    if request.method == "GET":
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '1':
            return render(request, 'TeaHistory.html')
        else:
            return render(request, 'login.html')

    elif request.method == "POST":
        login_user_code = request.session['user_code']  # 获取老师的账号
        login_dpartment_name_id=models.UserTable.objects.filter(user_code=login_user_code).first().dpartment_name_id  #获取当前的系号
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
        if request.session.get('is_login', False) and request.session.get('user_type', None) == '1':
            #登录成功后的操作
            user_code=request.session['user_code']   #获取操操作户账号
            obj = models.UserTable.objects.filter(user_code=user_code).first()  #查找用户相关信息
            return_dic={'user_code':obj.user_code,
                        'user_name': obj.user_name,
                        'dpartment_name':obj.dpartment_name.dpartement_name,
                        'stu_num':obj.stu_num,
                        'user_mail': obj.user_mail,
                        'user_phone': obj.user_phone,
                        'remark': obj.remark
            }
            return_dic['user_mail']='无' if obj.user_mail is None else obj.user_mail
            return_dic['user_phone']='无' if obj.user_phone is None else obj.user_phone
            return_dic['remark']='无' if obj.remark is None else obj.remark
            return render(request,'TeaPerson.html',return_dic)
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

