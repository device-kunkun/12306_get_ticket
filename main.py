from datetime import datetime
import json
import time
import threading

from bs4 import BeautifulSoup
from select import select
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import Select
import random
from fake_useragent import UserAgent
from lxml import etree


def simulate_drag_and_drop(source_element, target_element):
    action_chains = ActionChains(browser)
    action_chains.click_and_hold(source_element)  # 在源元素上点击并按住
    action_chains.move_to_element(target_element)  # 移动鼠标到目标元素
    action_chains.release(target_element)  # 释放鼠标点击
    action_chains.perform()  # 执行操作
    print("模拟拖动操作完成！")

class GetTicket:

    def __init__(self):
        with open('password_12306.json', 'r', encoding='utf-8') as f:
            user = json.load(f)
        self.username = user['username']
        self.password = user['password']
        self.idcard_last4 = user['idcard_last4']
        self.passenger_name = user["passenger_name"]
        self.login_url = 'https://kyfw.12306.cn/otn/resources/login.html'
        self.departure_time = '2024-12-03'
        self.departure_station = '深圳北'
        self.arrival_station = '长沙南'
        # 车次
        self.train_num = 'G6090'
        # 开始抢票时间
        self.scheduled_time = "2024-12-01 11:12:00"
        self.scheduled_time_strip = datetime.strptime(self.scheduled_time, "%Y-%m-%d %H:%M:%S")
        # 选择坐席
        self.seat_type = '一等座'
        ticket_list = {
            '商务座': '2',
            '特选一等座': '3',
            '一等座': '4',
            '二等座': '5',
            '软卧': '7',
            '硬卧': '8',
            '硬座': '10'
        }
        if int(ticket_list[self.seat_type]) <= 5:
            self.train_type = "高铁"
            # 位置（1A,1B,1C,1D,1F）
            self.seat_you_choose = user['seat_you_choose']  #位置（1A,1B,1C,1D,1F）
        elif int(ticket_list[self.seat_type]) == 7:
            self.train_type = "软卧"
        elif int(ticket_list[self.seat_type]) == 8:
            self.train_type = "硬卧"
        elif int(ticket_list[self.seat_type]) == 10:
            self.train_type == "硬座"
        self.seat_type_str =  ticket_list[self.seat_type]
        #是否勾选学生
        self.stu = ""
        self.is_student = False

        #是否勾选仅高铁/动车
        self.is_onlyfast = False
        #是否选择座位
        self.choose_seat = True


    # 定时
    def timing(self):
        flag = True
        while True:
            diff_time = (self.scheduled_time_strip - datetime.now()).seconds
            if diff_time > 60:
                print(f'当前时间：{datetime.now()}, 等待中。。。')
                time.sleep(10)
            elif diff_time < 30:
                flag = False
                print('抢票时间不足，退出程序')
                break
            else:
                print('还有60秒开始，启动主程序。。。')
                break
        return flag

    # 登录
    def login(self):
        browser.get(self.login_url)
        time.sleep(2)
        # 输入用户名
        browser.find_element(By.ID, 'J-userName').send_keys(self.username)
        # 输入密码
        browser.find_element(By.ID, 'J-password').send_keys(self.password)
        # 点击登录
        time.sleep(1)
        browser.find_element(By.ID, 'J-login').click()

        # 等待id_card输入框可交互
        WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.ID, 'id_card'))
        )

        # 滚动到输入框位置，确保它不被遮挡
        id_card_element = browser.find_element(By.ID, 'id_card')
        ActionChains(browser).move_to_element(id_card_element).perform()

        # 输入身份证后4位
        browser.find_element(By.ID, 'id_card').send_keys(self.idcard_last4)
        browser.find_element(By.ID, 'verification_code').click()

        # 启动一个新线程来等待验证码输入
        threading.Thread(target=self.wait_for_captcha_input, daemon=True).start()

        # 启动一个循环，保持浏览器打开直到验证码正确
        self.wait_for_captcha_success()

        browser.find_element(By.XPATH, '//*[@id="J-index"]/a').click()
        time.sleep(2)


    # 等待验证码输入
    def wait_for_captcha_input(self):
        while True:
            print("请输入验证码并按回车:")
            captcha = input("请输入验证码: ")
            # 输入验证码
            browser.find_element(By.ID, 'code').send_keys(captcha)
            # 点击确认按钮
            browser.find_element(By.ID, 'sureClick').click()

            # 检查是否出现验证码错误提示
            try:
                # 等待并检查验证码错误提示，假设错误提示的ID为'captcha-error'
                error_message = WebDriverWait(browser, 5).until(
                    EC.presence_of_element_located((By.ID, 'captcha-error'))
                )
                if error_message.is_displayed():
                    print("验证码错误，请重新输入...")
                    continue  # 重新输入验证码
            except:
                print("验证码输入成功，进入下一步！")
                break  # 验证码正确，退出循环

    # 保持浏览器打开直到验证码输入成功
    def wait_for_captcha_success(self):
        while True:
            try:
                # 检查验证码输入是否成功
                # 在这里你可以检查页面是否已经成功登录或跳转
                # 例如，检查是否存在登录成功的元素，或者检查某个页面的特征
                WebDriverWait(browser, 4).until(EC.presence_of_element_located((By.CLASS_NAME, 'welcome-con')))
                print("登录成功！")
                break
            except Exception as e:
                # 还没有成功登录，继续等待
                pass

            time.sleep(1)  # 等待1秒后继续检查



    # 在 query_ticket 方法或其他需要的地方集成
    def query_ticket(self):
        url = 'https://www.12306.cn/index/index.html'
        browser.get(url)
        time.sleep(random.uniform(3, 6))  # 页面加载时的等待时间

        # 等待直到元素可以点击

        # 模拟鼠标移动到页面的不同位置
        ActionChains(browser).move_by_offset(random.randint(0, 15), random.randint(0, 15)).perform()
        time.sleep(random.uniform(0.5, 1))

        # 模拟点击输入框以激活并拖动
        from_station = browser.find_element(By.ID, 'fromStationText')
        to_station = browser.find_element(By.ID, 'toStationText')

        ActionChains(browser).move_to_element(from_station).click().perform()
        time.sleep(random.uniform(0.5, 1))
        ActionChains(browser).move_to_element(to_station).click().perform()
        time.sleep(random.uniform(0.5, 1))

        # 模拟从 'from_station' 输入框拖动到 'to_station' 输入框
        simulate_drag_and_drop(from_station, to_station)

        # 输入出发地
        from_station.send_keys(Keys.CONTROL, 'a')
        from_station.send_keys(Keys.BACKSPACE)
        time.sleep(random.uniform(0.5, 1))  # 适当增加延迟
        for char in self.departure_station:
            from_station.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # 每个字符输入间的随机延时
        time.sleep(random.uniform(0.3, 0.6))
        from_station.send_keys(Keys.ENTER)

        # 输入到达地
        to_station.send_keys(Keys.CONTROL, 'a')
        to_station.send_keys(Keys.BACKSPACE)
        time.sleep(random.uniform(0.5, 1))
        for char in self.arrival_station:
            to_station.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))
        time.sleep(random.uniform(0.3, 0.6))
        to_station.send_keys(Keys.ENTER)

        # 输入出发日期
        train_date = browser.find_element(By.ID, 'train_date')
        train_date.send_keys(Keys.CONTROL, 'a')
        train_date.send_keys(Keys.BACKSPACE)
        time.sleep(random.uniform(0.5, 1))
        for char in self.departure_time:
            train_date.send_keys(char)
            time.sleep(random.uniform(0.1, 0.3))  # 每个字符输入间的随机延时
        time.sleep(random.uniform(0.3, 0.6))
        train_date.send_keys(Keys.ENTER)

        # 选择学生选项框
        student_checkbox = browser.find_element(By.ID, 'isStudentDan')

        # 如果is_student为True，勾选选项框；否则，取消勾选
        if self.is_student:
            if 'active' not in student_checkbox.get_attribute('class'):
                student_checkbox.click()  # 点击勾选
                print("学生选项已勾选")
            time.sleep(random.uniform(0.5, 1))
        else:
            if 'active' in student_checkbox.get_attribute('class'):
                student_checkbox.click()  # 点击取消勾选
                print("学生选项已取消勾选")
            time.sleep(random.uniform(0.5, 1))

        # 选择高铁选项框
        only_fast = browser.find_element(By.ID, 'isHighDan')
        if self.is_onlyfast:
            if 'active' not in only_fast.get_attribute('class'):
                only_fast.click()  # 点击勾选
                print("高铁选项已勾选")
            time.sleep(random.uniform(0.5, 1))
        else:
            if 'active' in only_fast.get_attribute('class'):
                only_fast.click()  # 点击取消勾选
                print("高铁选项已取消勾选")
            time.sleep(random.uniform(0.5, 1))

        # 模拟滚动
        browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(random.uniform(1, 2))

        # 点击查询按钮
        search_button = browser.find_element(By.ID, 'search_one')
        search_button.click()

        browser.switch_to.window(browser.window_handles[-1])
        time.sleep(random.uniform(3, 6))  # 加入随机等待，模拟用户的操作

        print("查询已提交，等待结果...")
        # browser.find_element(By.ID, 'query_ticket').click()
        # time.sleep(10)

    #baochidenglu
    def stay_login(self):
        # 点击按钮后，窗口可能发生变化，切换到新窗口

        time.sleep(2)
        #点击用户名，进入用户界面
        # 等待直到元素可点击
        WebDriverWait(browser, 8).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="toolbar_Div"]/div[2]/div[1]/div/div/ul/li[7]/a')))
        browser.find_element(By.XPATH, '//*[@id="toolbar_Div"]/div[2]/div[1]/div/div/ul/li[7]/a').click()

        time.sleep(10)

        while True:
            # 计算抢票时间
            diff_time = (self.scheduled_time_strip - datetime.now()).seconds
            if diff_time > 15:
                print('刷新用户信息，stay')
                browser.refresh()
                time.sleep(random.uniform(1, 2))
            else:
                print('进入购票')
                break

        browser.back()
        time.sleep(random.uniform(1, 2))


    def booking_ticket(self):
        success_flag = False
        # 点击查询按钮
        browser.find_element(By.ID, 'query_ticket').click()

        WebDriverWait(browser, 3, 0.01).until(EC.presence_of_element_located((By.XPATH, '//*[@id="queryLeftTable"]/tr')))
        page_text = browser.page_source
        html = etree.HTML(page_text)
        query_table = html.xpath('//*[@id="queryLeftTable"]/tr')
        for num in range(len(query_table) - 1):
            if num % 2 == 1:
                continue
            train_num_query = query_table[num].xpath('.//a[@class="number"]/text()')[0]
            departure_place_query = query_table[num].xpath('.//div[@class="cdz"]/strong[1]/text()')[0]
            arrival_place_query = query_table[num].xpath('.//div[@class="cdz"]/strong[2]/text()')[0]
            if train_num_query == self.train_num and departure_place_query == self.departure_station and arrival_place_query == self.arrival_station:
                print(f'have find {train_num_query}')
                ticket_left = query_table[num].xpath(f'.//td[{self.seat_type_str}]//text()')[0]
                if ticket_left == '有' or eval(ticket_left) >= 1:
                    print(f'find {self.train_num} -- {self.seat_type} have ticket')
                    #booking
                    browser.find_element(By.XPATH, f'//*[@id="queryLeftTable"]/tr[{num+1}]//td[13]/a').click()
                    print(f'已点击预定按钮，当前时间是：{datetime.now()}')

                    time.sleep(random.uniform(1, 2))

                    try:
                        # 检查是否存在带有 "(学生)" 的标签
                        student_label = WebDriverWait(browser, 3).until(
                            EC.presence_of_element_located((By.XPATH, f"//label[text()='{self.passenger_name}(学生)']"))
                        )
                        # 存在学生标签，执行学生相关任务
                        student_label.click()
                        self.stu = "学生"
                        print("点击了带有(学生)的标签，执行学生任务")

                    except Exception:
                        try:
                            # 如果没有带有(学生)的标签，检查是否存在只有乘客名字的标签
                            passenger_label = WebDriverWait(browser, 3).until(
                                EC.presence_of_element_located((By.XPATH, f"//label[text()='{self.passenger_name}']"))
                            )
                            # 存在只有乘客名字的标签，执行其他任务
                            passenger_label.click()
                            print("点击了没有(学生)的标签，执行其他任务")

                        except Exception:
                            # 如果既没有带(学生)的标签，也没有只有名字的标签，输出不存在
                            print("没有找到指定的乘客信息")
                    if self.stu == "学生":
                        if self.is_student:
                            browser.find_element(By.ID,'dialog_xsertcj_ok').click()
                            try:
                                # 等待警告框出现
                                warning_element = WebDriverWait(browser, 10).until(
                                    EC.presence_of_element_located((By.ID, 'content_defaultwarningAlert_hearder'))
                                )

                                # 如果警告框存在，点击关闭按钮
                                close_button = browser.find_element(By.ID, 'qd_closeDefaultWarningWindowDialog_id')
                                close_button.click()
                                print("学生票不足，自动选择成人票。")

                                select_element = WebDriverWait(browser, 10).until(
                                    EC.presence_of_element_located((By.ID, 'ticketType_1'))
                                )
                                select = Select(select_element)
                                select.select_by_value('1')  # 根据value值选择成人票
                                print("已选择成人票。")

                            except Exception as e:
                                print("没有出现警告", e)
                        else:
                            browser.find_element(By.ID,'dialog_xsertcj_cancel').click()
                            try:
                                # 等待警告框出现
                                warning_element = WebDriverWait(browser, 10).until(
                                    EC.presence_of_element_located((By.ID, 'content_defaultwarningAlert_hearder'))
                                )

                                # 如果警告框存在，点击关闭按钮
                                close_button = browser.find_element(By.ID, 'qd_closeDefaultWarningWindowDialog_id')
                                close_button.click()
                                print("警告框已关闭。")

                            except Exception as e:
                                print("没有出现警告框，或出现其他错误：", e)


                    #选择坐席
                    seat_type_ele = browser.find_element(By.ID, 'seatType_1')
                    seat_type_list = {
                        '一等座': 'M',
                        '二等座': 'O',
                        '商务座': '9',
                        '软卧': '4',
                        '硬卧': '3',
                        '硬座': '1',
                    }
                    seat_value = seat_type_list[self.seat_type]
                    Select(seat_type_ele).select_by_value(seat_value)

                    #提交订单
                    browser.find_element(By.ID, 'submitOrder_id').click()

                    if self.train_type == "高铁":
                        if self.choose_seat:
                            seat_btn =  WebDriverWait(browser, 6).until(
                                EC.element_to_be_clickable((By.ID,self.seat_you_choose))
                            )
                            seat_btn.click()
                    # 确认提交
                    submit_btn = WebDriverWait(browser, 6).until(
                        EC.element_to_be_clickable((By.ID, 'qr_submit_id'))
                    )
                    submit_btn.click()

                    success_flag = True

                else:
                    print(f'{self.train_num} -- {self.seat_type} no ticket')

                break
        return success_flag


    def run(self):
        #等待
        # self.timing()

        # 登录
        self.login()

        # 查询
        self.query_ticket()

        # 刷新
        # self.stay_login()

        # 预定
        self.booking_ticket()
        max_try = 3
        try_time = 0
        while True:
            if datetime.now() > self.scheduled_time_strip:
                print(f"进入抢票，当前时间{datetime.now()}")
                success_booking = self.booking_ticket()
                if success_booking:
                    print('抢票成功，尽快付款')
                    break
                elif try_time > max_try:
                    print('抢票失败')


        input("按任意键退出程序并关闭浏览器...")


if __name__ == '__main__':
    # 指定Chrome用户数据目录
    user_data_dir = r"C:/Users/Admin/AppData/Local/Google/Chrome/User Data"  # 替换为你自己的路径
    profile_dir = "Default" # 使用已登录的用户配置，修改为你实际的配置文件夹，通常是 "Default"

    ua = UserAgent()
    random_user_agent = ua.random
    # 设置Chrome选项
    opt = Options()
    # opt.add_experimental_option('excludeSwitches', ['enable-automation'])  # 屏蔽Chrome自动化受控提示
    # opt.add_argument("--disable-blink-features=AutomationControlled")  # 禁用启用Blink运行时的功能去掉webdriver痕迹
    # opt.add_experimental_option('useAutomationExtension', False)  # 禁用自动化扩展
    # opt.add_argument('--disable-dev-shm-usage')  # 禁用/dev/shm使用
    # opt.add_argument('--no-sandbox')  # 禁用沙箱
    # opt.add_argument('--start-maximized')  # 启动时最大化窗口
    # opt.add_argument('--disable-infobars')  # 禁用信息栏
    # opt.add_argument('--disable-notifications')  # 禁用通知
    # opt.add_argument('--disable-extensions')  # 禁用扩展
    opt.add_argument(f"user-agent={random_user_agent}")  # 随机设置 User-Agent

    opt.add_argument("--disable-blink-features=AutomationControlled")  # 禁用启用Blink运行时的功能去掉webdriver痕迹
    opt.debugger_address = "127.0.0.1:9222"   # chrome.exe --remote-debugging-port=9222
    # opt.add_argument(f"user-data-dir={user_data_dir}")  # 指定用户数据目录
    # opt.add_argument(f"profile-directory={profile_dir}")  # 指定使用的配置文件夹
    opt.page_load_strategy = 'eager'

    # 启动浏览器
    service = Service(ChromeDriverManager().install())
    browser = webdriver.Chrome(service=service, options=opt)
    print("浏览器已启动")
    # 禁用 WebDriver 属性
    # browser.execute_cdp_cmd('Network.setUserAgentOverride', {
    #     'userAgent': random_user_agent  # 使用 random User-Agent
    # })
    # browser.execute_cdp_cmd('Emulation.setScriptExecutionDisabled', {'value': True})

    get_ticket = GetTicket()
    get_ticket.run()
