import flet as ft
from Restaurante import Restaurante
from Mesa import Mesa
from Cliente import Cliente

class RestauranteGUI:
    def __init__(self):
        self.restaurante = Restaurante()
        capacidades = [2, 2, 4, 4, 6, 6]  # mesas y capacidades
        for i in range(1, 7):
            self.restaurante.agregar_mesa(Mesa(i, capacidades[i - 1]))

    def main(self, page: ft.Page):
        page.title = "Sistema restaurante"
        page.padding = 20
        page.theme_mode = "Dark"

        self.tabs = ft.Tabs(
            selected_index=0,
            animation_duration=300,
            tabs=[
                ft.Tab(
                    text="Mesera",
                    icon=ft.Icons.PERSON,
                    content=self.crear_vista_mesera()
                ),
                ft.Tab(
                    text="Cocina",
                    icon=ft.Icons.RESTAURANT,
                    content=self.crear_vista_cocina()
                ),
                ft.Tab(
                    text="Caja",
                    icon=ft.Icons.POINT_OF_SALE,
                    content=self.crear_vista_caja()
                ),
                ft.Tab(
                    text="Administracion",
                    icon=ft.Icons.ADMIN_PANEL_SETTINGS,
                    content=self.crear_vista_admin()
                ),
            ],
            expand=1
        )
        page.add(self.tabs)

    # ---------------- VISTAS ----------------
    def crear_vista_mesera(self):
        self.grid_container = ft.Container(
            content=self.crear_grid_mesas(),
            width=700,
            expand=True
        )
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.Column(
                        controls=[
                            ft.Text("Mesas del restaurante", size=20, weight=ft.FontWeight.BOLD),
                            self.grid_container
                        ]
                    ),
                    ft.VerticalDivider(),
                    ft.Container(
                        width=400,
                        content=self.crear_panel_gestion(),
                        expand=True
                    )
                ]
            )
        )

    def crear_vista_cocina(self):
        self.lista_pedidos_cocina = ft.ListView(
            expand=1,
            spacing=10,
            padding=20,
            auto_scroll=True,
        )
        return ft.Container(
            content=ft.Column([
                ft.Text("Pedidos en Cocina", size=20, weight=ft.FontWeight.BOLD),
                self.lista_pedidos_cocina
            ]),
            padding=20,
            expand=True
        )

    def actualizar_vista_cocina(self):
        self.lista_pedidos_cocina.controls.clear()
        for mesa in self.restaurante.mesas:
            if mesa.ocupada and mesa.pedido_actual:
                if mesa.pedido_actual.estado in ["Pendiente", "En preparacion"]:
                    self.lista_pedidos_cocina.controls.append(
                        self.crear_item_pedido_cocina(mesa.pedido_actual)
                    )

    def crear_item_pedido_cocina(self, pedido):
        def cambiar_estado_pedido(e, p, nuevo_estado):
            p.cambiar_estado(nuevo_estado)
            self.actualizar_vista_cocina()
            e.page.update()

        return ft.Container(
            content=ft.Column([
                ft.Text(f"Mesa {pedido.mesa.numero}", size=20, weight=ft.FontWeight.BOLD),
                ft.Text(pedido.obtener_resumen()),
                ft.Row([
                    ft.ElevatedButton(
                        "En preparacion",
                        on_click=lambda e, p=pedido: cambiar_estado_pedido(e, p, "En preparacion"),
                        disabled=pedido.estado != "Pendiente",
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.ORANGE_700,
                            color=ft.Colors.WHITE,
                        )
                    ),
                    ft.ElevatedButton(
                        "Listo",
                        on_click=lambda e, p=pedido: cambiar_estado_pedido(e, p, "Listo"),
                        disabled=pedido.estado != "En preparacion",
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_700,
                            color=ft.Colors.WHITE,
                        )
                    ),
                ]),
                ft.Text(f"Estado: {pedido.estado}", color=ft.Colors.BLUE_200)
            ]),
            bgcolor=ft.Colors.BLUE_GREY_900,
            padding=10,
            border_radius=10,
        )

    def crear_vista_caja(self):
        self.lista_caja = ft.ListView(
            expand=1,
            spacing=10,
            padding=20,
            auto_scroll=True,
        )

        def procesar_pago(e, mesa):
            if mesa.pedido_actual:
                self.restaurante.liberar_mesa(mesa.numero)
                self.actualizar_ui(e.page)

        def crear_item_cuenta(mesa):
            if not mesa.pedido_actual:
                return None

            return ft.Container(
                content=ft.Column([
                    ft.Text(f"Mesa {mesa.numero}", size=20, weight=ft.FontWeight.BOLD),
                    ft.Text(f"Cliente {mesa.cliente.id}"),
                    ft.Text(mesa.pedido_actual.obtener_resumen()),
                    ft.ElevatedButton(
                        "Procesar pago",
                        on_click=lambda e, m=mesa: procesar_pago(e, m),
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_700,
                            color=ft.Colors.WHITE,
                        )
                    )
                ]),
                bgcolor=ft.Colors.BLUE_GREY_900,
                padding=10,
                border_radius=10
            )

        def actualizar_vista_caja():
            self.lista_caja.controls.clear()
            for mesa in self.restaurante.mesas:
                if mesa.ocupada and mesa.pedido_actual:
                    item = crear_item_cuenta(mesa)
                    if item:
                        self.lista_caja.controls.append(item)
        self.actualizar_vista_caja = actualizar_vista_caja

        return ft.Container(
            content=ft.Column([
                ft.Text("Cuentas activas", size=24, weight=ft.FontWeight.BOLD),
                self.lista_caja
            ]),
            expand=True
        )

    # ---------------- VISTA ADMIN ----------------
    def crear_vista_admin(self):
        default_tipo = "Entrada"

        self.tipo_item_admin = ft.Dropdown(
            label="Tipo de item (Agregar)",
            options=[
                ft.dropdown.Option("Entrada"),
                ft.dropdown.Option("Plato Principal"),
                ft.dropdown.Option("Postre"),
                ft.dropdown.Option("Bebida"),
            ],
            value=default_tipo,
            width=250,
        )

        self.nombre_item = ft.TextField(
            label="Nombre de item",
            width=250,
        )

        # quitar filtro para permitir decimales y parsearlos nosotros
        self.precio_item = ft.TextField(
            label="Precio (usar . o , como separador decimal)",
            width=250,
        )

        self.tipo_item_eliminar = ft.Dropdown(
            label="Tipo item (Eliminar)",
            options=[
                ft.dropdown.Option("Entrada"),
                ft.dropdown.Option("Plato Principal"),
                ft.dropdown.Option("Postre"),
                ft.dropdown.Option("Bebida"),
            ],
            value=default_tipo,
            width=250,
            on_change=self.actualizar_items_eliminar
        )

        self.item_eliminar = ft.Dropdown(
            label="Seleccionar item a eliminar",
            width=300,
        )

        # Inicializar listas (no requiere page event)
        self.actualizar_items_eliminar(None)

        # Contenido
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Agregar item al menú", size=20, weight=ft.FontWeight.BOLD),
                    self.tipo_item_admin,
                    self.nombre_item,
                    self.precio_item,
                    ft.ElevatedButton(
                        text="Agregar item",
                        on_click=self.agregar_item,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.GREEN_700,
                            color=ft.Colors.WHITE,
                        )
                    ),
                    ft.Divider(),
                    ft.Text("Eliminar item del menú", size=20, weight=ft.FontWeight.BOLD),
                    self.tipo_item_eliminar,
                    self.item_eliminar,
                    ft.ElevatedButton(
                        text="Eliminar item",
                        on_click=self.eliminar_item,
                        style=ft.ButtonStyle(
                            bgcolor=ft.Colors.RED_700,
                            color=ft.Colors.WHITE,
                        )
                    ),
                ],
                spacing=12
            ),
            padding=20,
            bgcolor=ft.Colors.BLUE_GREY_900
        )

    # helper: mostrar snackbar
    def _show_snack(self, page, text, ok=True):
        page.snack_bar = ft.SnackBar(
            ft.Text(text),
            bgcolor=ft.Colors.GREEN_700 if ok else ft.Colors.RED_700
        )
        page.snack_bar.open = True
        page.update()

    def agregar_item(self, e):
        tipo = self.tipo_item_admin.value
        nombre = (self.nombre_item.value or "").strip()
        texto_precio = (self.precio_item.value or "").strip()

        if not tipo or not nombre or not texto_precio:
            self._show_snack(e.page, "Completa tipo, nombre y precio.", ok=False)
            return

        # aceptar coma o punto como separador decimal
        texto_precio = texto_precio.replace(",", ".")
        try:
            precio = float(texto_precio)
        except ValueError:
            self._show_snack(e.page, "Precio inválido. Usa números (ej: 120 o 12.50).", ok=False)
            return

        if precio <= 0:
            self._show_snack(e.page, "El precio debe ser mayor a 0.", ok=False)
            return

        # Llamar al método correcto del menu (asegúrate que existan en Restaurante.menu)
        if tipo == "Entrada":
            self.restaurante.menu.agregar_entrada(nombre, precio)
        elif tipo == "Plato Principal":
            self.restaurante.menu.agregar_plato_principal(nombre, precio)
        elif tipo == "Postre":
            self.restaurante.menu.agregar_postre(nombre, precio)
        elif tipo == "Bebida":
            self.restaurante.menu.agregar_bebida(nombre, precio)
        else:
            self._show_snack(e.page, f"Tipo desconocido: {tipo}", ok=False)
            return

        # limpiar campos
        self.nombre_item.value = ""
        self.precio_item.value = ""

        # refrescar dropdowns (si existen)
        if hasattr(self, 'tipo_item_dropdown'):
            self.actualizar_items_menu(None)
        self.actualizar_items_eliminar(None)

        self._show_snack(e.page, f"Item '{nombre}' agregado ({tipo})")
        e.page.update()

    def eliminar_item(self, e):
        tipo = self.tipo_item_eliminar.value
        nombre = self.item_eliminar.value
        if not tipo or not nombre:
            self._show_snack(e.page, "Selecciona tipo y item a eliminar.", ok=False)
            return

        # eliminar (asegúrate que exista Restaurante.menu.eliminar_item)
        self.restaurante.menu.eliminar_item(tipo, nombre)

        # refrescar dropdowns
        if hasattr(self, 'tipo_item_dropdown'):
            self.actualizar_items_menu(None)
        self.actualizar_items_eliminar(None)

        self._show_snack(e.page, f"Item '{nombre}' eliminado ({tipo})")
        e.page.update()

    def actualizar_items_eliminar(self, e):
        tipo = getattr(self, "tipo_item_eliminar", None) and self.tipo_item_eliminar.value
        if tipo == "Entrada":
            items = self.restaurante.menu.entradas
        elif tipo == "Plato Principal":
            items = self.restaurante.menu.platos_principales
        elif tipo == "Postre":
            items = self.restaurante.menu.postres
        elif tipo == "Bebida":
            items = self.restaurante.menu.bebidas
        else:
            items = []

        self.item_eliminar.options = [ft.dropdown.Option(item.nombre) for item in items]
        # resetear valor para evitar que quede un valor inválido
        self.item_eliminar.value = None

        if e and getattr(e, "page", None):
            e.page.update()

    # --------------- GESTIÓN MESAS ---------------
    def crear_grid_mesas(self):
        grid = ft.GridView(
            expand=1,
            runs_count=2,
            max_extent=200,
            child_aspect_ratio=1.0,
            spacing=10,
            run_spacing=10,
            padding=10,
        )

        for mesa in self.restaurante.mesas:
            color = ft.Colors.GREEN_700 if not mesa.ocupada else ft.Colors.RED_700
            estado = "LIBRE" if not mesa.ocupada else "OCUPADA"

            grid.controls.append(
                ft.Container(
                    bgcolor=color,
                    border_radius=10,
                    padding=15,
                    ink=True,
                    on_click=lambda e, num=mesa.numero: self.seleccionar_mesa(e, num),
                    content=ft.Column(
                        alignment=ft.MainAxisAlignment.CENTER,
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=5,
                        controls=[
                            ft.Row(
                                alignment=ft.MainAxisAlignment.CENTER,
                                controls=[
                                    ft.Icon(ft.Icons.TABLE_RESTAURANT, color=ft.Colors.AMBER_400),
                                    ft.Text(f"Mesa {mesa.numero}", size=16, weight=ft.FontWeight.BOLD),
                                ]
                            ),
                            ft.Text(f"Capacidad: {mesa.tamaño}", size=12),
                            ft.Text(estado, size=14, weight=ft.FontWeight.BOLD)
                        ]
                    )
                )
            )
        return grid

    def actualizar_ui(self, page):
        nuevo_grid = self.crear_grid_mesas()
        self.grid_container.content = nuevo_grid

        if self.mesa_seleccionada:
            if self.mesa_seleccionada.ocupada and self.mesa_seleccionada.pedido_actual:
                self.resumen_pedido.value = self.mesa_seleccionada.pedido_actual.obtener_resumen()
            else:
                self.resumen_pedido.value = ""

            self.asignar_btn.disabled = self.mesa_seleccionada.ocupada
            self.agregar_item_btn.disabled = not self.mesa_seleccionada.ocupada
            self.liberar_btn.disabled = not self.mesa_seleccionada.ocupada

        if hasattr(self, 'lista_pedidos_cocina'):
            self.actualizar_vista_cocina()
        if hasattr(self, 'lista_caja'):
            self.actualizar_vista_caja()

        page.update()

    def seleccionar_mesa(self, e, numero_mesa):
        self.mesa_seleccionada = self.restaurante.buscar_mesa(numero_mesa)
        mesa = self.mesa_seleccionada
        self.mesa_info.value = f"Mesa {mesa.numero} - Capacidad: {mesa.tamaño} personas"

        self.asignar_btn.disabled = mesa.ocupada
        self.agregar_item_btn.disabled = not mesa.ocupada
        self.liberar_btn.disabled = not mesa.ocupada

        if mesa.ocupada and mesa.pedido_actual:
            self.resumen_pedido.value = mesa.pedido_actual.obtener_resumen()
        else:
            self.resumen_pedido.value = ""

        e.page.update()
        return None

    def crear_panel_gestion(self):
        self.mesa_seleccionada = None
        self.mesa_info = ft.Text("", size=16, weight=ft.FontWeight.BOLD)
        self.tamaño_grupo_input = ft.TextField(
            label="Tamaño del grupo",
            input_filter=ft.NumbersOnlyInputFilter(),
            prefix_icon=ft.Icons.PEOPLE
        )

        self.tipo_item_dropdown = ft.Dropdown(
            label="Tipo de item",
            options=[
                ft.dropdown.Option("Entrada"),
                ft.dropdown.Option("Plato Principal"),
                ft.dropdown.Option("Postre"),
                ft.dropdown.Option("Bebida"),
            ],
            value="Entrada",
            width=200,
            on_change=self.actualizar_items_menu
        )
        self.items_dropdown = ft.Dropdown(
            label="Seleccionar item",
            width=200,
        )

        self.asignar_btn = ft.ElevatedButton(
            text="Asignar Cliente",
            on_click=self.asignar_cliente,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.GREEN_700,
                color=ft.Colors.WHITE,
            )
        )

        self.agregar_item_btn = ft.ElevatedButton(
            text="Agregar Item",
            on_click=self.agregar_item_pedido,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.BLUE_700,
                color=ft.Colors.WHITE,
            )
        )

        self.liberar_btn = ft.ElevatedButton(
            text="Liberar Mesa",
            on_click=self.liberar_mesa,
            disabled=True,
            style=ft.ButtonStyle(
                bgcolor=ft.Colors.RED_700,
                color=ft.Colors.WHITE,
            )
        )

        self.resumen_pedido = ft.Text("", size=14)

        # Inicializar items del menú en Mesera
        self.actualizar_items_menu(None)

        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Container(
                        content=self.mesa_info,
                        bgcolor=ft.Colors.BLUE_GREY_900,
                        padding=10,
                        border_radius=10,
                    ),
                    ft.Container(height=20),
                    self.tamaño_grupo_input,
                    self.asignar_btn,
                    ft.Divider(),
                    self.tipo_item_dropdown,
                    self.items_dropdown,
                    self.agregar_item_btn,
                    ft.Divider(),
                    self.liberar_btn,
                    ft.Divider(),
                    ft.Text("Resumen del pedido", size=16, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        content=self.resumen_pedido,
                        bgcolor=ft.Colors.BLUE_GREY_900,
                        padding=10,
                        border_radius=10,
                    )
                ],
                spacing=10,
                expand=True,
            ),
            padding=20,
            expand=True
        )

    def asignar_cliente(self, e):
        if not self.mesa_seleccionada:
            return
        if not self.tamaño_grupo_input.value:
            return
        try:
            tamaño_grupo = int(self.tamaño_grupo_input.value)
        except ValueError:
            return
        if tamaño_grupo <= 0:
            return

        cliente = Cliente(tamaño_grupo)
        resultado = self.restaurante.asignar_cliente_a_mesa(cliente, self.mesa_seleccionada.numero)

        if "asignado" in resultado:
            self.restaurante.crear_pedido(self.mesa_seleccionada.numero)
            self.tamaño_grupo_input.value = ""
            self.actualizar_ui(e.page)

    def actualizar_items_menu(self, e):
        tipo = getattr(self, "tipo_item_dropdown", None) and self.tipo_item_dropdown.value
        if tipo == "Entrada":
            items = self.restaurante.menu.entradas
        elif tipo == "Plato Principal":
            items = self.restaurante.menu.platos_principales
        elif tipo == "Postre":
            items = self.restaurante.menu.postres
        elif tipo == "Bebida":
            items = self.restaurante.menu.bebidas
        else:
            items = []

        self.items_dropdown.options = [ft.dropdown.Option(item.nombre) for item in items]
        self.items_dropdown.value = None

        if e and getattr(e, "page", None):
            e.page.update()

    def agregar_item_pedido(self, e):
        if not self.mesa_seleccionada or not self.mesa_seleccionada.pedido_actual:
            return

        tipo = self.tipo_item_dropdown.value
        nombre_item = self.items_dropdown.value

        if tipo and nombre_item:
            item = self.restaurante.obtener_item_menu(tipo, nombre_item)
            if item:
                self.mesa_seleccionada.pedido_actual.agregar_item(item)
                self.resumen_pedido.value = self.mesa_seleccionada.pedido_actual.obtener_resumen()
                self.actualizar_ui(e.page)

    def liberar_mesa(self, e):
        if self.mesa_seleccionada:
            self.restaurante.liberar_mesa(self.mesa_seleccionada.numero)
            self.actualizar_ui(e.page)


def main():
    app = RestauranteGUI()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()
