import asyncio
import logging
import json

from flask import Flask, request
from telegram import Update
from telegram.ext import Application, CallbackContext, CommandHandler

# Configurar logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Token de tu bot
TOKEN = 'INGRESA EL TOKEN DE TU BOT'

# Inicializar la aplicación de Flask
app = Flask(__name__)

# Función para obtener el ID del chat
async def start(update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id if update.message else update.callback_query.message.chat_id
    await update.message.reply_text(f'Tu ID de chat es {chat_id}')

async def user_info(update: Update, context: CallbackContext) -> None:
    # Verificar si se proporcionó un usuario mencionado
    if not context.args:
        await update.message.reply_text("Debes mencionar a un usuario después del comando /info.")
        return

    # Obtener el nombre de usuario mencionado
    mentioned_username = context.args[0].lstrip('@')

    try:
        # Obtener información del chat para buscar al usuario mencionado
        chat_id = update.message.chat_id
        mentioned_user = None
        is_admin = False

        # Buscar el usuario mencionado en la lista de administradores del chat
        for member in await context.bot.get_chat_administrators(chat_id=chat_id):
            if member.user.username == mentioned_username:
                mentioned_user = member.user
                is_admin = True
                break

        # Si no se encuentra en la lista de administradores, buscar en la lista de miembros del chat
        if not mentioned_user:
            member_count = await context.bot.get_chat_member_count(chat_id)
            for user_id in range(1, member_count + 1):
                try:
                    member = await context.bot.get_chat_member(chat_id, user_id)
                    if member.user.username == mentioned_username:
                        mentioned_user = member.user
                        break
                except:
                    continue

        if not mentioned_user:
            await update.message.reply_text(f"No se pudo encontrar al usuario @{mentioned_username}.")
            return

        user_id = mentioned_user.id

        # Inicializar el diccionario de información del usuario
        user_info_dict = {}

        user_object = update.message.from_user if update.message else update.inline_query.from_user

        # Obtener el código de idioma del usuario
        user_language_code = getattr(user_object, 'language_code', "No disponible")

        # Obtener la biografía del usuario si está disponible
        user_info_dict = getattr(mentioned_user, 'bio', None)
        if user_info_dict is None:
            user_info_dict = "No disponible"

        # Determinar si el número de teléfono está oculto
        phone_hidden = hasattr(mentioned_user, 'phone_number') and mentioned_user.phone_number is None

        # Determinar si el número de teléfono está visible
        phone_number = mentioned_user.phone_number if hasattr(mentioned_user, 'phone_number') else None
        phone_hidden = phone_number is None

        # Función para formatear el número de teléfono con el prefijo "+"
        def format_phone_number(phone_number):
            return f"+{phone_number}" if phone_number else "No disponible"

        try:
            # Obtener el objeto ChatMember del usuario
            chat_member = await context.bot.get_chat_member(chat_id=chat_id, user_id=user_id)

            # Llenar el diccionario con la información del usuario
            user_info_dict = {
    "Username": f"@{chat_member.user.username}" if chat_member.user.username else "No disponible",
    "Apellido": "No tiene apellidos" if mentioned_user.last_name is None else mentioned_user.last_name,
    "Idioma": user_language_code, 
    "Telefono": format_phone_number(phone_number) if not phone_hidden else "Oculto",
    "Descripcion": user_info_dict,
    "Bot": f"@{chat_member.user.username}" if chat_member.user.is_bot else "No, es un usuario",
    "Puede unirse a grupos": getattr(chat_member.user, 'can_join_groups', "No disponible"),
    "Puede leer todos los mensajes de grupo": getattr(chat_member.user, 'can_read_all_group_messages', "No disponible"),
    "Admite consultas en linea": getattr(chat_member.user, 'supports_inline_queries', "No disponible"),
    "ID": chat_member.user.id,
    "Administrador": "si" if chat_member.status in ['administrator', 'creator'] else "no",
    "Situacion": chat_member.status if chat_member.status else "No disponible",
    "Alias": getattr(chat_member.user, 'alias', "No disponible"),         
  "Unido": datetime.fromtimestamp(chat_member.joined_date).strftime('%d/%m/%Y %H:%M:%S') if hasattr(chat_member, 'joined_date') else "No disponible"
            }
        except Exception as e:
            # Si ocurre un error, agregar un mensaje de error al diccionario
            user_info_dict["Error"] = f"No se pudo obtener la información del usuario. Error: {e}"

        # Convertir el diccionario a JSON
        user_info_json = json.dumps(user_info_dict, indent=4)

        # Enviar el resultado en un archivo .json
        with open("user_info.json", "w") as json_file:
            json_file.write(user_info_json)

        if "Error" in user_info_dict:
            await update.message.reply_text(f"No se pudo obtener la información del usuario. Error: {user_info_dict['Error']}")
        else:
            # Enviar el mensaje de confirmación
            await update.message.reply_text(f"Información del usuario:\n{user_info_json}")

    except Exception as e:
        await update.message.reply_text(f"No se pudo encontrar al usuario mencionado. Error: {e}")

# Manejador de ruta para mostrar el HTML
@app.route('/show_html', methods=['POST'])
def show_html():
    html = request.form['html']
    return html

# Función principal para iniciar el bot
async def main() -> None:
    application = Application.builder().token(TOKEN).build()

    # Configurar manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", user_info))

    # Iniciar el bot
    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    # Mantener el bot corriendo
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        # Detener el bot si se interrumpe con Ctrl+C
        pass

if __name__ == '__main__':
    # Ejecutar la aplicación de Flask en un hilo separado
    import threading
    threading.Thread(target=app.run, kwargs={'debug': False}).start()
    # Ejecutar el bucle de eventos de asyncio
    asyncio.run(main())
