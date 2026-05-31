import sys, os, uuid, pymysql
from PyQt6 import QtWidgets, QtGui
from PyQt6.QtCore import Qt, QDate

# БАЗА ДАННЫХ
DB_CONFIG = {'host': 'localhost', 'user': 'root', 'password': 'root1', 'database': 'shos5',
             'charset': 'utf8mb4', 'cursorclass': pymysql.cursors.DictCursor}

# ФУНКЦИЯ ВЫПОЛНЕНИЯ SQL-ЗАПРОСОВ
def sql(query, params=None, fetch_one=False, fetch_all=False, commit=False):
    conn = pymysql.connect(**DB_CONFIG)
    cur = conn.cursor()
    cur.execute(query, params or ())
    if commit:
        conn.commit()
        res = cur.rowcount
    else:
        res = cur.fetchone() if fetch_one else cur.fetchall() if fetch_all else None
    cur.close()
    conn.close()
    return res

# ЗАГРУЗКА ДАННЫХ В ВЫПАДАЮЩИЕ СПИСКИ
def load_combo(combo, table, id_field, name_field):
    for row in sql(f"SELECT {id_field}, {name_field} FROM {table}", fetch_all=True):
        combo.addItem(row[name_field], row[id_field])

# ПОКАЗ СООБЩЕНИЙ
def show_msg(parent, title, text, icon=QtWidgets.QMessageBox.Icon.Information):
    mb = QtWidgets.QMessageBox(parent)
    mb.setWindowTitle(title); mb.setText(text); mb.setIcon(icon); mb.exec()

# ===== ЗАГРУЗКА ЛОГОТИПА И ИКОНКИ =====
def get_logo_pixmap():
    return QtGui.QPixmap('logo.png') if os.path.exists('logo.png') else None

def get_app_icon():
    if os.path.exists('app_icon.ico'): return QtGui.QIcon('app_icon.ico')
    if os.path.exists('app_icon.png'): return QtGui.QIcon('app_icon.png')
    return None

# ===== ФОРМА ДОБАВЛЕНИЯ/РЕДАКТИРОВАНИЯ ТОВАРА =====
class ProductForm(QtWidgets.QDialog):
    def __init__(self, product=None, parent=None):
        super().__init__(parent)
        self.product = product          # редактируемый товар (если есть)
        self.image_path = None          # путь к выбранному фото
        self.setWindowTitle("Добавление товара" if not product else "Редактирование товара")
        self.setMinimumSize(500, 650)
        self.setStyleSheet("QDialog{background:#FFF;font-family:'Times New Roman'} QLineEdit,QComboBox,QTextEdit{background:#7FFF00} QPushButton{background:#00FA9A;border:none;padding:8px} QPushButton:hover{background:#2E8B57;color:#FFF}")
        if get_app_icon(): self.setWindowIcon(get_app_icon())
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel(self.windowTitle()); title.setStyleSheet("font-size:16px;font-weight:bold"); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        form = QtWidgets.QFormLayout()
        # Поля ввода
        self.name = QtWidgets.QLineEdit()
        self.cat = QtWidgets.QComboBox(); load_combo(self.cat, 'Categories', 'CategoryID', 'Name')
        self.man = QtWidgets.QComboBox(); load_combo(self.man, 'Manufacturers', 'ManufacturerID', 'Name')
        self.sup = QtWidgets.QComboBox(); load_combo(self.sup, 'Suppliers', 'SupplierID', 'Name')
        self.unit = QtWidgets.QLineEdit("шт")
        self.desc = QtWidgets.QTextEdit(); self.desc.setMaximumHeight(80)
        self.price = QtWidgets.QLineEdit()
        self.stock = QtWidgets.QLineEdit()
        self.discount = QtWidgets.QLineEdit()
        form.addRow("Наименование:", self.name); form.addRow("Категория:", self.cat)
        form.addRow("Производитель:", self.man); form.addRow("Поставщик:", self.sup)
        form.addRow("Единица измерения:", self.unit); form.addRow("Описание:", self.desc)
        form.addRow("Цена (руб.):", self.price); form.addRow("Кол-во (шт):", self.stock); form.addRow("Скидка (%):", self.discount)
        # Блок выбора фото
        self.img_label = QtWidgets.QLabel("Нет фото")
        self.img_label.setFixedSize(150,100); self.img_label.setStyleSheet("border:1px solid #7FFF00;background:#f0f0f0")
        self.img_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        btn_img = QtWidgets.QPushButton("Выбрать фото"); btn_img.clicked.connect(self.choose_image)
        form.addRow("Фото:", self.img_label); form.addRow("", btn_img)
        layout.addLayout(form)
        # Кнопки OK / Cancel
        btns = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Сохранить"); btn_ok.clicked.connect(self.accept)
        btn_cancel = QtWidgets.QPushButton("Отмена"); btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok); btns.addWidget(btn_cancel)
        layout.addLayout(btns)
        if product: self.load_data()

    def load_data(self):
        """Заполняет поля при редактировании существующего товара"""
        self.name.setText(self.product['Name'])
        self.price.setText(str(self.product['Price']))
        self.stock.setText(str(self.product['StockQuantity']))
        self.discount.setText(str(self.product.get('Discount',0)))
        self.desc.setPlainText(self.product.get('Description',''))
        self.unit.setText(self.product.get('Unit','шт'))
        for combo, field in [(self.cat,'CategoryID'), (self.man,'ManufacturerID'), (self.sup,'SupplierID')]:
            idx = combo.findData(self.product[field])
            if idx>=0: combo.setCurrentIndex(idx)
        if self.product.get('ImagePath') and os.path.exists(self.product['ImagePath']):
            self.image_path = self.product['ImagePath']
            self.img_label.setPixmap(QtGui.QPixmap(self.image_path).scaled(150,100))

    def choose_image(self):
        """Открывает диалог выбора фото, копирует его в папку uploads"""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Фото", "", "Images (*.png *.jpg *.jpeg)")
        if path:
            os.makedirs('uploads', exist_ok=True)
            ext = os.path.splitext(path)[1]
            save = os.path.join('uploads', uuid.uuid4().hex+ext)
            pix = QtGui.QPixmap(path).scaled(300,200, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            pix.save(save)
            self.image_path = save
            self.img_label.setPixmap(pix.scaled(150,100))

    def get_data(self):
        """Возвращает кортеж со значениями полей"""
        return (self.name.text().strip(), self.cat.currentData(), self.man.currentData(), self.sup.currentData(),
                self.unit.text().strip(), self.desc.toPlainText(), float(self.price.text() or 0),
                int(self.stock.text() or 0), float(self.discount.text() or 0), self.image_path)

# ===== ФОРМА ДОБАВЛЕНИЯ/РЕДАКТИРОВАНИЯ ЗАКАЗА =====
class OrderDialog(QtWidgets.QDialog):
    def __init__(self, order=None, parent=None):
        super().__init__(parent)
        self.order = order
        is_edit = order is not None
        self.setWindowTitle("Редактирование заказа" if is_edit else "Добавление заказа")
        self.setFixedSize(450,400)
        self.setStyleSheet("QDialog{background:#FFF;font-family:'Times New Roman'} QLineEdit,QComboBox,QDateEdit{background:#7FFF00} QPushButton{background:#00FA9A;border:none;padding:8px} QPushButton:hover{background:#2E8B57;color:#FFF}")
        if get_app_icon(): self.setWindowIcon(get_app_icon())
        layout = QtWidgets.QVBoxLayout(self)
        title = QtWidgets.QLabel(self.windowTitle()); title.setStyleSheet("font-size:16px;font-weight:bold"); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        form = QtWidgets.QFormLayout()
        if is_edit:
            # Режим редактирования: клиент не меняется, показываем только статус, адрес и дату выдачи
            user = sql("SELECT FullName FROM Users WHERE UserID=%s", (order['UserID'],), fetch_one=True)
            user_label = QtWidgets.QLabel(user['FullName'] if user else "Гость")
            user_label.setStyleSheet("background-color:#f0f0f0;padding:5px")
            form.addRow("Клиент:", user_label)
            self.status_combo = QtWidgets.QComboBox()
            self.status_combo.addItems(['Новый','В обработке','Готов к выдаче','Выдан'])
            self.status_combo.setCurrentText(order['Status'])
            form.addRow("Статус:", self.status_combo)
            self.address_edit = QtWidgets.QLineEdit(order['DeliveryAddress'])
            form.addRow("Адрес:", self.address_edit)
            order_date_label = QtWidgets.QLabel(str(order['OrderDate']))
            order_date_label.setStyleSheet("background-color:#f0f0f0;padding:5px")
            form.addRow("Дата заказа:", order_date_label)
            self.issue_date = QtWidgets.QDateEdit(); self.issue_date.setCalendarPopup(True)
            if order['IssueDate']: self.issue_date.setDate(QDate.fromString(str(order['IssueDate']),'yyyy-MM-dd'))
            else: self.issue_date.setDate(QDate.currentDate())
            form.addRow("Дата выдачи:", self.issue_date)
        else:
            # Режим добавления: все поля активны
            self.user_combo = QtWidgets.QComboBox()
            for u in sql("SELECT UserID, FullName FROM Users", fetch_all=True):
                self.user_combo.addItem(u['FullName'], u['UserID'])
            form.addRow("Клиент:", self.user_combo)
            self.status_combo = QtWidgets.QComboBox()
            self.status_combo.addItems(['Новый','В обработке','Готов к выдаче','Выдан'])
            form.addRow("Статус:", self.status_combo)
            self.address_edit = QtWidgets.QLineEdit(); self.address_edit.setPlaceholderText("Адрес пункта выдачи")
            form.addRow("Адрес:", self.address_edit)
            self.order_date = QtWidgets.QDateEdit(); self.order_date.setCalendarPopup(True); self.order_date.setDate(QDate.currentDate())
            form.addRow("Дата заказа:", self.order_date)
            self.issue_date = QtWidgets.QDateEdit(); self.issue_date.setCalendarPopup(True); self.issue_date.setDate(QDate.currentDate())
            form.addRow("Дата выдачи:", self.issue_date)
        layout.addLayout(form)
        btns = QtWidgets.QHBoxLayout()
        btn_ok = QtWidgets.QPushButton("Сохранить"); btn_ok.clicked.connect(self.accept)
        btn_cancel = QtWidgets.QPushButton("Отмена"); btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok); btns.addWidget(btn_cancel)
        layout.addLayout(btns)

    def get_data(self):
        """Возвращает кортеж данных в зависимости от режима (добавление/редактирование)"""
        if hasattr(self, 'user_combo'):
            return (self.user_combo.currentData(), self.status_combo.currentText(), self.address_edit.text(),
                    self.order_date.date().toString('yyyy-MM-dd'), self.issue_date.date().toString('yyyy-MM-dd'))
        else:
            return (self.status_combo.currentText(), self.address_edit.text(),
                    self.issue_date.date().toString('yyyy-MM-dd'))

# ===== ВИДЖЕТ КАРТОЧКИ ТОВАРА =====
class ProductCard(QtWidgets.QWidget):
    def __init__(self, product, is_admin, show_cart_btn, on_edit, on_delete, on_add_to_cart, parent=None):
        super().__init__(parent)
        self.product = product
        self.setMinimumHeight(200); self.setMaximumHeight(240)
        self.setStyleSheet("QWidget{background:#FFF;border:none;border-radius:5px;margin:2px} QLabel{font-family:'Times New Roman';background:transparent}")
        main_layout = QtWidgets.QHBoxLayout(self); main_layout.setContentsMargins(15,10,15,10); main_layout.setSpacing(20)
        # Левая часть: фото
        photo = QtWidgets.QLabel(); photo.setFixedSize(150,150); photo.setStyleSheet("border:1px solid #000;background:#f0f0f0")
        path = product.get('ImagePath')
        pix = QtGui.QPixmap(path).scaled(150,150,Qt.AspectRatioMode.KeepAspectRatio) if path and os.path.exists(path) else QtGui.QPixmap(150,150)
        if not path or not os.path.exists(path): pix.fill(QtGui.QColor('#CCCCCC'))
        photo.setPixmap(pix); main_layout.addWidget(photo)
        # Центральная часть: информация о товаре
        info_widget = QtWidgets.QWidget(); info_layout = QtWidgets.QVBoxLayout(info_widget); info_layout.setSpacing(5)
        info_layout.addWidget(QtWidgets.QLabel(f"{product.get('CategoryName','')} | {product['Name']}", styleSheet="font-size:14px;font-weight:bold"))
        info_layout.addWidget(QtWidgets.QLabel(f"Описание товара: {product.get('Description','')}", wordWrap=True))
        info_layout.addWidget(QtWidgets.QLabel(f"Производитель: {product.get('ManufacturerName','')}"))
        info_layout.addWidget(QtWidgets.QLabel(f"Поставщик: {product.get('SupplierName','')}"))
        price, disc = product['Price'], product.get('Discount',0)
        price_txt = f"Цена: <span style='text-decoration:line-through;color:red;'>{price:,.2f} руб.</span> | {price*(1-disc/100):,.2f} руб." if disc>0 else f"Цена: {price:,.2f} руб."
        price_lbl = QtWidgets.QLabel(price_txt); price_lbl.setTextFormat(Qt.TextFormat.RichText)
        info_layout.addWidget(price_lbl)
        qty_layout = QtWidgets.QHBoxLayout()
        qty_layout.addWidget(QtWidgets.QLabel(f"Единицы измерения: {product.get('Unit','шт')}"))
        qty_layout.addSpacing(30); qty_layout.addWidget(QtWidgets.QLabel(f"Количество на складе: {product['StockQuantity']}"))
        qty_layout.addStretch(); info_layout.addLayout(qty_layout)
        # Кнопки для администратора
        if is_admin:
            admin_btns = QtWidgets.QHBoxLayout()
            btn_edit = QtWidgets.QPushButton("Редактировать товар"); btn_edit.setFixedHeight(35); btn_edit.setMinimumWidth(150)
            btn_edit.setStyleSheet("background-color:#00FA9A;color:black;font-weight:bold;border:none;border-radius:5px")
            btn_edit.clicked.connect(lambda: on_edit(product['ProductID']))
            btn_del = QtWidgets.QPushButton("Удалить товар"); btn_del.setFixedHeight(35); btn_del.setMinimumWidth(150)
            btn_del.setStyleSheet("background-color:#00FA9A;color:black;font-weight:bold;border:none;border-radius:5px")
            btn_del.clicked.connect(lambda: on_delete(product['ProductID']))
            admin_btns.addWidget(btn_edit); admin_btns.addWidget(btn_del); admin_btns.addStretch()
            info_layout.addLayout(admin_btns)
        main_layout.addWidget(info_widget, stretch=1)
        # Правая панель: скидка и кнопка "В корзину"
        right_panel = QtWidgets.QWidget(); right_panel.setFixedWidth(150); right_panel.setFixedHeight(160)
        right_layout = QtWidgets.QVBoxLayout(right_panel); right_layout.setAlignment(Qt.AlignmentFlag.AlignCenter); right_layout.setSpacing(10); right_layout.setContentsMargins(0,0,0,0)
        discount_block = QtWidgets.QWidget(); discount_block.setFixedHeight(80)
        discount_layout = QtWidgets.QVBoxLayout(discount_block); discount_layout.setAlignment(Qt.AlignmentFlag.AlignCenter); discount_layout.setSpacing(5)
        if disc>0:
            discount_title = QtWidgets.QLabel("Действующая скидка"); discount_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            discount_title.setStyleSheet("font-size:12px;font-weight:bold;color:#2E8B57;background:transparent")
            discount_layout.addWidget(discount_title)
            discount_value = QtWidgets.QLabel(f"{disc:.0f}%"); discount_value.setAlignment(Qt.AlignmentFlag.AlignCenter)
            discount_value.setStyleSheet("font-size:32px;font-weight:bold;color:#2E8B57;background:transparent")
            discount_layout.addWidget(discount_value)
        else:
            discount_layout.addWidget(QtWidgets.QLabel(" ")); discount_layout.addWidget(QtWidgets.QLabel(" "))
        right_layout.addWidget(discount_block)
        if show_cart_btn:
            cart_btn = QtWidgets.QPushButton("В корзину"); cart_btn.setFixedHeight(40); cart_btn.setFixedWidth(120)
            cart_btn.setStyleSheet("background-color:#00FA9A;color:black;font-weight:bold;font-size:13px;border:none;border-radius:8px")
            cart_btn.setCursor(QtGui.QCursor(Qt.CursorShape.PointingHandCursor))
            cart_btn.clicked.connect(lambda: on_add_to_cart(product['ProductID'], product['Name'], price*(1-disc/100) if disc>0 else price))
            right_layout.addWidget(cart_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(right_panel)
        # Подсветка фона при большой скидке или нулевом остатке
        if disc>15:
            self.setStyleSheet("QWidget{background:#2E8B57;border:none;border-radius:5px;margin:2px} QLabel{color:white;background:transparent}")
            discount_title.setStyleSheet("font-size:12px;font-weight:bold;color:white;background:transparent")
            discount_value.setStyleSheet("font-size:32px;font-weight:bold;color:white;background:transparent")
        elif product['StockQuantity']==0:
            self.setStyleSheet("QWidget{background:#D4E6F1;border:none;border-radius:5px;margin:2px} QLabel{color:black;background:transparent}")

# ===== ОКНО КОРЗИНЫ =====
class CartWindow(QtWidgets.QMainWindow):
    def __init__(self, cart_items, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.cart_items = cart_items   # список товаров в корзине
        self.setWindowTitle("Корзина"); self.setGeometry(300,300,650,500)
        self.setStyleSheet("QMainWindow{background:#FFF;font-family:'Times New Roman'} QPushButton{background:#00FA9A;padding:8px;border:none} QPushButton:hover{background:#2E8B57;color:#FFF} QTableWidget{alternate-background-color:#7FFF00}")
        if get_app_icon(): self.setWindowIcon(get_app_icon())
        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        self.table = QtWidgets.QTableWidget(); self.table.setColumnCount(4); self.table.setHorizontalHeaderLabels(['ID','Название','Цена','Количество'])
        self.table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        bottom = QtWidgets.QHBoxLayout()
        self.total_label = QtWidgets.QLabel("Итого: 0.00 руб."); self.total_label.setStyleSheet("font-size:16px;font-weight:bold")
        bottom.addWidget(self.total_label); bottom.addStretch()
        self.btn_clear = QtWidgets.QPushButton("Очистить корзину"); self.btn_clear.clicked.connect(self.clear_cart)
        bottom.addWidget(self.btn_clear)
        self.btn_checkout = QtWidgets.QPushButton("Оформить заказ"); self.btn_checkout.clicked.connect(self.checkout)
        bottom.addWidget(self.btn_checkout)
        layout.addLayout(bottom)
        self.load_cart()

    def load_cart(self):
        """Обновляет таблицу корзины и пересчитывает итоговую сумму"""
        self.table.setRowCount(len(self.cart_items))
        total = 0
        for row, item in enumerate(self.cart_items):
            self.table.setItem(row,0, QtWidgets.QTableWidgetItem(str(item['id'])))
            self.table.setItem(row,1, QtWidgets.QTableWidgetItem(item['name']))
            self.table.setItem(row,2, QtWidgets.QTableWidgetItem(f"{item['price']:.2f} руб."))
            qty_widget = QtWidgets.QWidget(); qty_layout = QtWidgets.QHBoxLayout(qty_widget); qty_layout.setContentsMargins(0,0,0,0)
            btn_minus = QtWidgets.QPushButton("-"); btn_minus.setFixedSize(30,30); btn_minus.setStyleSheet("background-color:#00FA9A;")
            btn_minus.clicked.connect(lambda checked, r=row: self.change_quantity(r, -1))
            qty_label = QtWidgets.QLabel(str(item['quantity'])); qty_label.setAlignment(Qt.AlignmentFlag.AlignCenter); qty_label.setMinimumWidth(30)
            btn_plus = QtWidgets.QPushButton("+"); btn_plus.setFixedSize(30,30); btn_plus.setStyleSheet("background-color:#00FA9A;")
            btn_plus.clicked.connect(lambda checked, r=row: self.change_quantity(r, 1))
            qty_layout.addWidget(btn_minus); qty_layout.addWidget(qty_label); qty_layout.addWidget(btn_plus)
            self.table.setCellWidget(row,3, qty_widget)
            total += item['price'] * item['quantity']
        self.total_label.setText(f"Итого: {total:.2f} руб.")

    def change_quantity(self, row, delta):
        """Изменяет количество товара в корзине (+1 / -1)"""
        new_qty = self.cart_items[row]['quantity'] + delta
        if new_qty < 1:
            self.cart_items.pop(row)
        else:
            self.cart_items[row]['quantity'] = new_qty
        self.load_cart()

    def clear_cart(self):
        """Очищает корзину"""
        self.cart_items.clear(); self.load_cart()
        if self.parent_window: self.parent_window.update_cart_count()

    def checkout(self):
        """Оформляет заказ: создаёт запись в Orders и OrderItems, уменьшает остатки"""
        if not self.cart_items: show_msg(self, "Ошибка", "Корзина пуста", QtWidgets.QMessageBox.Icon.Warning); return
        for item in self.cart_items:
            prod = sql("SELECT StockQuantity FROM Products WHERE ProductID=%s", (item['id'],), fetch_one=True)
            if not prod or prod['StockQuantity'] < item['quantity']: show_msg(self, "Ошибка", f"Товара '{item['name']}' нет в нужном количестве", QtWidgets.QMessageBox.Icon.Warning); return
        user_id = None
        if self.parent_window and hasattr(self.parent_window, 'user'):
            user = self.parent_window.user
            if user.get('Role') == 'guest': user_id = None
            elif user.get('UserID'): user_id = user['UserID']
        order_date = QDate.currentDate().toString('yyyy-MM-dd')
        try:
            conn = pymysql.connect(**DB_CONFIG)
            cur = conn.cursor()
            cur.execute("INSERT INTO Orders (UserID, Status, DeliveryAddress, OrderDate, IssueDate) VALUES (%s,%s,%s,%s,%s)", (user_id, 'Новый', 'Адрес не указан', order_date, None))
            conn.commit()
            cur.execute("SELECT LAST_INSERT_ID() as id")
            order_id = cur.fetchone()['id']
            for item in self.cart_items:
                cur.execute("INSERT INTO OrderItems (OrderID, ProductID, Quantity) VALUES (%s,%s,%s)", (order_id, item['id'], item['quantity']))
                cur.execute("UPDATE Products SET StockQuantity = StockQuantity - %s WHERE ProductID=%s", (item['quantity'], item['id']))
            conn.commit()
            cur.close(); conn.close()
            self.cart_items.clear(); self.load_cart()
            show_msg(self, "Успех", f"Заказ №{order_id} оформлен!", QtWidgets.QMessageBox.Icon.Information)
            if self.parent_window:
                self.parent_window.load_products()
                self.parent_window.update_cart_count()
                if hasattr(self.parent_window, 'orders_win') and self.parent_window.orders_win:
                    self.parent_window.orders_win.load_orders()
            self.close()
        except Exception as e: show_msg(self, "Ошибка", f"Ошибка: {str(e)}", QtWidgets.QMessageBox.Icon.Critical)

# ===== ДИАЛОГ ПРОСМОТРА ТОВАРОВ В ЗАКАЗЕ =====
class OrderItemsDialog(QtWidgets.QDialog):
    def __init__(self, order_id, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Товары в заказе №{order_id}")
        self.setMinimumSize(500,400)
        self.setStyleSheet("QDialog{background:#FFF;font-family:'Times New Roman'} QTableWidget{alternate-background-color:#7FFF00}")
        layout = QtWidgets.QVBoxLayout(self)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['ID товара','Наименование','Количество'])
        self.table.setEditTriggers(QtWidgets.QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)
        btn_close = QtWidgets.QPushButton("Закрыть"); btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignCenter)
        items = sql("SELECT oi.ProductID, p.Name, oi.Quantity FROM OrderItems oi JOIN Products p ON oi.ProductID=p.ProductID WHERE oi.OrderID=%s", (order_id,), fetch_all=True) or []
        self.table.setRowCount(len(items))
        for r,item in enumerate(items):
            self.table.setItem(r,0, QtWidgets.QTableWidgetItem(str(item['ProductID'])))
            self.table.setItem(r,1, QtWidgets.QTableWidgetItem(item['Name']))
            self.table.setItem(r,2, QtWidgets.QTableWidgetItem(str(item['Quantity'])))
        self.table.resizeColumnsToContents()

# ===== ОКНО УПРАВЛЕНИЯ ЗАКАЗАМИ =====
class OrdersWindow(QtWidgets.QMainWindow):
    def __init__(self, user, parent=None):
        super().__init__(parent)
        self.user = user
        self.setWindowTitle("Заказы клиентов"); self.setGeometry(200,200,900,500)
        self.setStyleSheet("QMainWindow{background:#FFF;font-family:'Times New Roman'} QPushButton{background:#00FA9A;border:none;padding:5px} QPushButton:hover{background:#2E8B57;color:#FFF} QTableWidget{alternate-background-color:#7FFF00}")
        if get_app_icon(): self.setWindowIcon(get_app_icon())
        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("Добавить заказ"); self.btn_add.clicked.connect(self.add_order)
        self.btn_edit = QtWidgets.QPushButton("Редактировать"); self.btn_edit.clicked.connect(self.edit_order)
        self.btn_del = QtWidgets.QPushButton("Удалить"); self.btn_del.clicked.connect(self.delete_order)
        if user.get('Role') != 'admin':  # только админ может управлять заказами
            for b in (self.btn_add, self.btn_edit, self.btn_del): b.setVisible(False)
        btn_row.addWidget(self.btn_add); btn_row.addWidget(self.btn_edit); btn_row.addWidget(self.btn_del)
        layout.addLayout(btn_row)
        self.table = QtWidgets.QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(['ID','Клиент','Статус','Адрес','Дата заказа','Дата выдачи'])
        self.table.cellDoubleClicked.connect(lambda r,c: OrderItemsDialog(int(self.table.item(r,0).text()), self).exec())
        layout.addWidget(self.table)
        self.load_orders()

    def load_orders(self):
        """Загружает список заказов из БД"""
        orders = sql("SELECT o.OrderID, u.FullName, o.Status, o.DeliveryAddress, o.OrderDate, o.IssueDate FROM Orders o LEFT JOIN Users u ON o.UserID=u.UserID ORDER BY o.OrderDate DESC, o.OrderID DESC", fetch_all=True) or []
        self.table.setRowCount(len(orders))
        for r,o in enumerate(orders):
            self.table.setItem(r,0, QtWidgets.QTableWidgetItem(str(o['OrderID'])))
            self.table.setItem(r,1, QtWidgets.QTableWidgetItem(o['FullName'] if o['FullName'] else 'Гость'))
            self.table.setItem(r,2, QtWidgets.QTableWidgetItem(o['Status']))
            self.table.setItem(r,3, QtWidgets.QTableWidgetItem(o['DeliveryAddress']))
            self.table.setItem(r,4, QtWidgets.QTableWidgetItem(str(o['OrderDate'])))
            self.table.setItem(r,5, QtWidgets.QTableWidgetItem(str(o['IssueDate']) if o['IssueDate'] else ''))

    def add_order(self):
        dlg = OrderDialog(parent=self)
        if dlg.exec():
            data = dlg.get_data()
            sql("INSERT INTO Orders (UserID,Status,DeliveryAddress,OrderDate,IssueDate) VALUES (%s,%s,%s,%s,%s)", data, commit=True)
            self.load_orders()

    def edit_order(self):
        row = self.table.currentRow()
        if row<0: show_msg(self, "Ошибка", "Выберите заказ", QtWidgets.QMessageBox.Icon.Warning); return
        oid = int(self.table.item(row,0).text())
        order = sql("SELECT * FROM Orders WHERE OrderID=%s", (oid,), fetch_one=True)
        if order:
            dlg = OrderDialog(order, self)
            if dlg.exec():
                status, addr, issue = dlg.get_data()
                sql("UPDATE Orders SET Status=%s, DeliveryAddress=%s, IssueDate=%s WHERE OrderID=%s", (status, addr, issue, oid), commit=True)
                self.load_orders()
                show_msg(self, "Успех", "Заказ обновлён", QtWidgets.QMessageBox.Icon.Information)

    def delete_order(self):
        row = self.table.currentRow()
        if row<0: show_msg(self, "Ошибка", "Выберите заказ", QtWidgets.QMessageBox.Icon.Warning); return
        oid = int(self.table.item(row,0).text())
        if QtWidgets.QMessageBox.question(self, "Подтверждение", "Удалить заказ?") == QtWidgets.QMessageBox.StandardButton.Yes:
            sql("DELETE FROM OrderItems WHERE OrderID=%s", (oid,), commit=True)
            sql("DELETE FROM Orders WHERE OrderID=%s", (oid,), commit=True)
            self.load_orders()

# ===== ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ =====
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, user):
        super().__init__()
        self.user = user                      # данные текущего пользователя
        self.edit_window_open = False         # флаг для предотвращения повторного открытия формы редактирования
        self.orders_win = None
        self.cart = []                        # корзина (список товаров)
        role = user.get('Role', 'guest')
        title_suffix = " - Панель администратора" if role=='admin' else " - Панель менеджера" if role=='manager' else " - Каталог товаров"
        self.setWindowTitle("ООО Обувь" + title_suffix)
        self.setGeometry(100,100,1100,700)
        self.setStyleSheet("QMainWindow{background:#FFF} QLabel{font-family:'Times New Roman';color:#000} QPushButton{background:#00FA9A;padding:5px;border:none} QPushButton:hover{background:#2E8B57;color:#FFF} QLineEdit,QComboBox{background:#7FFF00}")
        if get_app_icon(): self.setWindowIcon(get_app_icon())
        central = QtWidgets.QWidget(); self.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)
        # Верхняя панель (логотип, корзина, ФИО, выход)
        top = QtWidgets.QHBoxLayout()
        logo_pix = get_logo_pixmap()
        if logo_pix:
            logo_label = QtWidgets.QLabel(); logo_label.setPixmap(logo_pix.scaled(100,50,Qt.AspectRatioMode.KeepAspectRatio)); logo_label.setFixedSize(100,50)
            top.addWidget(logo_label)
        else:
            top.addWidget(QtWidgets.QLabel("ООО Обувь", styleSheet="font-size:18px;font-weight:bold"))
        top.addStretch()
        self.btn_cart = QtWidgets.QPushButton("Корзина (0)")
        self.btn_cart.setStyleSheet("background-color:#00FA9A;padding:5px 15px;font-weight:bold;border-radius:5px")
        self.btn_cart.clicked.connect(self.open_cart)
        if role not in ['client','guest']: self.btn_cart.setVisible(False)
        top.addWidget(self.btn_cart)
        top.addWidget(QtWidgets.QLabel(user['FullName'], styleSheet="font-weight:bold"))
        self.btn_logout = QtWidgets.QPushButton("Выйти"); self.btn_logout.clicked.connect(self.close)
        top.addWidget(self.btn_logout); layout.addLayout(top)
        # Заголовок панели
        panel_title = "Панель администратора" if role=='admin' else "Панель менеджера" if role=='manager' else "Каталог товаров"
        layout.addWidget(QtWidgets.QLabel(panel_title, alignment=Qt.AlignmentFlag.AlignCenter, styleSheet="font-size:16px;font-weight:bold;margin:5px"))
        # Строка поиска, сортировки и фильтра
        flt = QtWidgets.QHBoxLayout()
        flt.addWidget(QtWidgets.QLabel("Поиск:")); self.search = QtWidgets.QLineEdit(); self.search.setPlaceholderText("Введите текст..."); self.search.textChanged.connect(self.load_products); flt.addWidget(self.search)
        flt.addWidget(QtWidgets.QLabel("Сортировка:")); self.sort = QtWidgets.QComboBox(); self.sort.addItems(["По умолчанию","По цене (возр.)","По цене (уб.)","По кол-ву (возр.)","По кол-ву (уб.)"]); self.sort.currentTextChanged.connect(self.load_products); flt.addWidget(self.sort)
        flt.addWidget(QtWidgets.QLabel("Поставщик:")); self.filter = QtWidgets.QComboBox(); self.filter.currentTextChanged.connect(self.load_products); flt.addWidget(self.filter); flt.addStretch()
        layout.addLayout(flt)
        # Кнопки "Добавить товар" и "Заказы клиентов" (доступны в зависимости от роли)
        btn_row = QtWidgets.QHBoxLayout()
        self.btn_add = QtWidgets.QPushButton("Добавить товар"); self.btn_add.clicked.connect(self.add_product)
        self.btn_orders = QtWidgets.QPushButton("Заказы клиентов"); self.btn_orders.clicked.connect(self.open_orders)
        btn_row.addWidget(self.btn_add); btn_row.addWidget(self.btn_orders); btn_row.addStretch()
        layout.addLayout(btn_row)
        # Область прокрутки для карточек товаров
        self.scroll = QtWidgets.QScrollArea(); self.scroll.setWidgetResizable(True); self.scroll.setStyleSheet("QScrollArea{border:none;background:#FFF}")
        self.products_widget = QtWidgets.QWidget(); self.products_layout = QtWidgets.QVBoxLayout(self.products_widget); self.products_layout.setSpacing(10); self.products_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.products_widget); layout.addWidget(self.scroll)
        # Настройка видимости кнопок в зависимости от роли
        if role == 'admin': self.btn_add.setVisible(True); self.btn_orders.setVisible(True)
        elif role == 'manager': self.btn_add.setVisible(False); self.btn_orders.setVisible(True)
        else: self.btn_add.setVisible(False); self.btn_orders.setVisible(False)
        self.load_suppliers(); self.load_products()

    def update_cart_count(self):
        """Обновляет надпись на кнопке корзины"""
        total_items = sum(item['quantity'] for item in self.cart)
        self.btn_cart.setText(f"Корзина ({total_items})")

    def add_to_cart(self, product_id, name, price):
        """Добавляет товар в корзину (или увеличивает количество)"""
        for item in self.cart:
            if item['id'] == product_id:
                item['quantity'] += 1; self.update_cart_count()
                show_msg(self, "Корзина", f"Товар '{name}' добавлен в корзину", QtWidgets.QMessageBox.Icon.Information); return
        self.cart.append({'id':product_id, 'name':name, 'price':price, 'quantity':1})
        self.update_cart_count()
        show_msg(self, "Корзина", f"Товар '{name}' добавлен в корзину", QtWidgets.QMessageBox.Icon.Information)

    def open_cart(self): self.cart_window = CartWindow(self.cart, self); self.cart_window.show()

    def load_suppliers(self):
        """Загружает список поставщиков для фильтра"""
        sup = sql("SELECT Name FROM Suppliers ORDER BY Name", fetch_all=True)
        self.filter.clear(); self.filter.addItem("Все поставщики")
        for s in sup: self.filter.addItem(s['Name'])

    def load_products(self):
        """Загружает и отображает товары с учётом поиска, сортировки и фильтра"""
        search = self.search.text(); supplier = self.filter.currentText(); sort_by = self.sort.currentText()
        query = """SELECT p.*, c.Name as CategoryName, m.Name as ManufacturerName, s.Name as SupplierName
                   FROM Products p JOIN Categories c ON p.CategoryID=c.CategoryID
                   JOIN Manufacturers m ON p.ManufacturerID=m.ManufacturerID
                   JOIN Suppliers s ON p.SupplierID=s.SupplierID WHERE 1=1"""
        params = []
        if search:
            query += " AND (p.Name LIKE %s OR p.Description LIKE %s OR m.Name LIKE %s OR s.Name LIKE %s)"
            like = f'%{search}%'; params.extend([like,like,like,like])
        if supplier and supplier!="Все поставщики": query += " AND s.Name=%s"; params.append(supplier)
        order = {"По цене (возр.)":"p.Price ASC","По цене (уб.)":"p.Price DESC","По кол-ву (возр.)":"p.StockQuantity ASC","По кол-ву (уб.)":"p.StockQuantity DESC"}.get(sort_by, "p.ProductID")
        query += f" ORDER BY {order}"
        prods = sql(query, params, fetch_all=True)
        # Очищаем старые карточки
        for i in reversed(range(self.products_layout.count())):
            w = self.products_layout.itemAt(i).widget()
            if w: w.deleteLater()
        is_admin = self.user.get('Role') == 'admin'
        show_cart_btn = self.user.get('Role') in ['client','guest']
        for p in prods:
            self.products_layout.addWidget(ProductCard(p, is_admin, show_cart_btn, self.edit_product, self.delete_product, self.add_to_cart, self))

    def add_product(self):
        """Открывает форму добавления товара"""
        dlg = ProductForm(parent=self)
        if dlg.exec():
            name,cat,man,sup,unit,desc,price,qty,disc,img = dlg.get_data()
            if not name or price<=0: show_msg(self, "Ошибка", "Заполните название и цену", QtWidgets.QMessageBox.Icon.Warning); return
            sql("INSERT INTO Products (Name,CategoryID,ManufacturerID,SupplierID,Unit,Description,Price,StockQuantity,Discount,ImagePath) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (name,cat,man,sup,unit,desc,price,qty,disc,img), commit=True)
            self.load_products()

    def edit_product(self, pid):
        """Открывает форму редактирования товара"""
        if self.edit_window_open: show_msg(self, "Внимание", "Окно редактирования уже открыто", QtWidgets.QMessageBox.Icon.Warning); return
        prod = sql("SELECT * FROM Products WHERE ProductID=%s", (pid,), fetch_one=True)
        if prod:
            dlg = ProductForm(prod, self)
            self.edit_window_open = True
            if dlg.exec():
                name,cat,man,sup,unit,desc,price,qty,disc,img = dlg.get_data()
                old_img = prod.get('ImagePath')
                if img and img!=old_img and old_img and os.path.exists(old_img):
                    try: os.remove(old_img)
                    except: pass
                sql("UPDATE Products SET Name=%s,CategoryID=%s,ManufacturerID=%s,SupplierID=%s,Unit=%s,Description=%s,Price=%s,StockQuantity=%s,Discount=%s,ImagePath=%s WHERE ProductID=%s",
                    (name,cat,man,sup,unit,desc,price,qty,disc,img,pid), commit=True)
                self.load_products()
            self.edit_window_open = False

    def delete_product(self, pid):
        """Удаляет товар, если он не связан с заказами"""
        if sql("SELECT * FROM OrderItems WHERE ProductID=%s", (pid,), fetch_all=True):
            show_msg(self, "Ошибка", "Товар есть в заказах, удалить нельзя", QtWidgets.QMessageBox.Icon.Critical); return
        if QtWidgets.QMessageBox.question(self, "Подтверждение", "Удалить товар?") == QtWidgets.QMessageBox.StandardButton.Yes:
            prod = sql("SELECT ImagePath FROM Products WHERE ProductID=%s", (pid,), fetch_one=True)
            if prod and prod.get('ImagePath') and os.path.exists(prod['ImagePath']):
                try: os.remove(prod['ImagePath'])
                except: pass
            sql("DELETE FROM Products WHERE ProductID=%s", (pid,), commit=True)
            self.load_products()

    def open_orders(self): self.orders_win = OrdersWindow(self.user, self); self.orders_win.show()

# ===== ОКНО АВТОРИЗАЦИИ =====
class LoginWindow(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Авторизация - ООО Обувь"); self.setFixedSize(400,350)
        self.setStyleSheet("QWidget{background:#FFF;font-family:'Times New Roman'} QLineEdit{background:#7FFF00;padding:5px} QPushButton{background:#00FA9A;padding:8px;border:none} QPushButton:hover{background:#2E8B57;color:#FFF}")
        if get_app_icon(): self.setWindowIcon(get_app_icon())
        layout = QtWidgets.QVBoxLayout(self)
        top = QtWidgets.QHBoxLayout()
        logo_pix = get_logo_pixmap()
        if logo_pix:
            logo_label = QtWidgets.QLabel(); logo_label.setPixmap(logo_pix.scaled(80,50,Qt.AspectRatioMode.KeepAspectRatio)); logo_label.setFixedSize(80,50)
            top.addWidget(logo_label)
        else:
            top.addWidget(QtWidgets.QLabel("ООО Обувь", styleSheet="font-size:16px;font-weight:bold"))
        top.addStretch(); layout.addLayout(top)
        layout.addWidget(QtWidgets.QLabel("Вход в систему", styleSheet="font-size:14px;margin-top:20px;margin-bottom:20px", alignment=Qt.AlignmentFlag.AlignCenter))
        self.login = QtWidgets.QLineEdit(); self.login.setPlaceholderText("Логин"); layout.addWidget(self.login)
        self.passwd = QtWidgets.QLineEdit(); self.passwd.setPlaceholderText("Пароль"); self.passwd.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password); layout.addWidget(self.passwd)
        btn_login = QtWidgets.QPushButton("Войти"); btn_login.clicked.connect(self.auth); layout.addWidget(btn_login)
        btn_guest = QtWidgets.QPushButton("Войти как гость"); btn_guest.clicked.connect(self.guest_login); layout.addWidget(btn_guest)
        self.error = QtWidgets.QLabel(); self.error.setStyleSheet("color:red"); self.error.setAlignment(Qt.AlignmentFlag.AlignCenter); layout.addWidget(self.error)

    def auth(self):
        """Проверка логина/пароля в БД"""
        user = sql("SELECT * FROM Users WHERE Login=%s AND Password=%s", (self.login.text().strip(), self.passwd.text().strip()), fetch_one=True)
        if user: self.open_main(user)
        else: self.error.setText("Неверный логин или пароль")

    def guest_login(self): self.open_main({'UserID':1, 'Login':'guest', 'FullName':'Гость', 'Role':'guest'})

    def open_main(self, user):
        self.main = MainWindow(user); self.main.show(); self.close()

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    win = LoginWindow(); win.show()
    sys.exit(app.exec())