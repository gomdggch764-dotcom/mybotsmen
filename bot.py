@bot.message_handler(commands=['withdraw'])
def withdraw(msg):
    uid = msg.from_user.id
    user = get_user(uid)
    if not user:
        bot.send_message(msg.chat.id, "❌ Введите /start")
        return
    if user[18]:
        bot.send_message(msg.chat.id, "❌ Вы забанены!")
        return
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "❌ Укажите сумму: /withdraw 120")
        return
    try:
        amount = float(args[1])
    except:
        bot.send_message(msg.chat.id, "❌ Введите число")
        return
    if amount < WITHDRAW_MIN:
        bot.send_message(msg.chat.id, f"❌ Минимум: {WITHDRAW_MIN} ⭐")
        return
    if amount > user[4]:
        bot.send_message(msg.chat.id, f"❌ Недостаточно! У вас: {user[4]:.1f} ⭐")
        return
    
    # Сохраняем заявку
    new_balance = user[4] - amount
    new_withdrawn = user[6] + amount
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET balance = ?, total_withdrawn = ? WHERE telegram_id = ?",
              (new_balance, new_withdrawn, uid))
    now = datetime.datetime.now().isoformat()
    c.execute("INSERT INTO withdrawals (user_id, amount, requested_at) VALUES (?,?,?)",
              (user[0], amount, now))
    conn.commit()
    conn.close()
    
    # Отправляем инструкцию
    bot.send_message(msg.chat.id,
        f"📝 ЗАЯВКА НА ВЫВОД: {amount} ⭐\n\n"
        f"✅ Заявка создана!\n"
        f"💰 Остаток на балансе: {new_balance:.1f} ⭐\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📹 ДЛЯ ПОЛУЧЕНИЯ ВЫПЛАТЫ:\n\n"
        f"Снимите видео длительностью от 30 секунд\n\n"
        f"Вариант 1 (TikTok):\n"
        f"Снимите видео в TikTok и в описании укажите:\n"
        f"«@EarnSaveliyBot выручает звёздами! Лучший бот для заработка 🔥»\n\n"
        f"Вариант 2 (любая соцсеть):\n"
        f"Снимите обзор бота — покажите как зарабатываете\n\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"📤 Отправьте видео сюда в чат\n"
        f"👑 Админ проверит и начислит выплату\n\n"
        f"⚠️ Видео должно быть реальным, без монтажа чужих роликов!",
        reply_markup=main_kb())
    
    # Ждём видео от пользователя
    bot.register_next_step_handler(msg, check_withdraw_video, amount)

def check_withdraw_video(msg, amount):
    uid = msg.from_user.id
    
    # Проверяем есть ли видео
    if not msg.video and not msg.video_note and not msg.animation:
        # Если отправил не видео
        bot.send_message(msg.chat.id,
            f"❌ Нужно отправить ВИДЕО!\n\n"
            f"📹 Снимите видео от 30 секунд:\n"
            f"• TikTok с описанием «@EarnSaveliyBot выручает звёздами»\n"
            f"• Или обзор бота\n\n"
            f"Отправьте видео файлом или ссылкой на TikTok",
            reply_markup=main_kb())
        bot.register_next_step_handler(msg, check_withdraw_video, amount)
        return
    
    # Видео получено — отправляем админу на проверку
    video = msg.video or msg.video_note or msg.animation
    user_info = f"@{msg.from_user.username or '—'} ({msg.from_user.id})"
    
    # Отправляем админам
    for admin_id in ADMIN_IDS:
        try:
            if msg.video:
                bot.send_video(admin_id, msg.video.file_id,
                    caption=f"📹 ЗАЯВКА НА ВЫВОД\n\n"
                    f"👤 Пользователь: {user_info}\n"
                    f"💰 Сумма: {amount} ⭐\n"
                    f"📅 Дата: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"✅ /approve {uid} {amount}\n"
                    f"❌ /reject {uid}")
            elif msg.video_note:
                bot.send_video_note(admin_id, msg.video_note.file_id)
                bot.send_message(admin_id,
                    f"📹 ЗАЯВКА НА ВЫВОД\n\n"
                    f"👤 Пользователь: {user_info}\n"
                    f"💰 Сумма: {amount} ⭐\n\n"
                    f"✅ /approve {uid} {amount}\n"
                    f"❌ /reject {uid}")
            elif msg.animation:
                bot.send_animation(admin_id, msg.animation.file_id,
                    caption=f"📹 ЗАЯВКА НА ВЫВОД\n\n"
                    f"👤 Пользователь: {user_info}\n"
                    f"💰 Сумма: {amount} ⭐\n\n"
                    f"✅ /approve {uid} {amount}\n"
                    f"❌ /reject {uid}")
        except Exception as e:
            logging.error(f"Ошибка отправки админу: {e}")
    
    bot.send_message(msg.chat.id,
        f"✅ ВИДЕО ОТПРАВЛЕНО!\n\n"
        f"📹 Ваше видео отправлено на проверку\n"
        f"💰 Сумма: {amount} ⭐\n\n"
        f"⏳ Ожидайте проверки админом\n"
        f"📩 Вы получите уведомление после проверки",
        reply_markup=main_kb())

# Команда для админа — одобрить
@bot.message_handler(commands=['approve'])
def approve_withdraw(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    args = msg.text.split()
    if len(args) < 3:
        bot.send_message(msg.chat.id, "❌ Формат: /approve [user_id] [amount]")
        return
    try:
        target_uid = int(args[1])
        amount = float(args[2])
    except:
        bot.send_message(msg.chat.id, "❌ Неверные данные")
        return
    
    # Обновляем статус в БД
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE withdrawals SET status = 'completed', completed_at = ? WHERE user_id = ? AND amount = ? AND status = 'pending'",
              (datetime.datetime.now().isoformat(), target_uid, amount))
    conn.commit()
    conn.close()
    
    # Уведомляем пользователя
    try:
        bot.send_message(target_uid,
            f"✅ ВЫПЛАТА ОДОБРЕНА!\n\n"
            f"💰 Сумма: {amount} ⭐\n"
            f"🎉 Поздравляем! Выплата будет отправлена в ближайшее время",
            reply_markup=main_kb())
    except:
        pass
    
    bot.send_message(msg.chat.id, f"✅ Выплата {amount} ⭐ для {target_uid} одобрена!")

# Команда для админа — отклонить
@bot.message_handler(commands=['reject'])
def reject_withdraw(msg):
    if msg.from_user.id not in ADMIN_IDS:
        return
    args = msg.text.split()
    if len(args) < 2:
        bot.send_message(msg.chat.id, "❌ Формат: /reject [user_id]")
        return
    try:
        target_uid = int(args[1])
    except:
        bot.send_message(msg.chat.id, "❌ Неверный ID")
        return
    
    # Находим сумму
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT amount FROM withdrawals WHERE user_id = ? AND status = 'pending' ORDER BY id DESC LIMIT 1", (target_uid,))
    result = c.fetchone()
    conn.close()
    
    if result:
        amount = result[0]
        # Возвращаем средства
        user = get_user(target_uid)
        if user:
            update_user(target_uid, balance=user[4] + amount)
    
    # Уведомляем пользователя
    try:
        bot.send_message(target_uid,
            f"❌ ВЫПЛАТА ОТКЛОНЕНА\n\n"
            f"😔 К сожалению, ваше видео не прошло проверку\n"
            f"💰 Сумма {amount} ⭐ возвращена на баланс\n\n"
            f"📹 Попробуйте снять новое видео:\n"
            f"• От 30 секунд\n"
            f"• Реальное, не скопированное\n"
            f"• С упоминанием @EarnSaveliyBot",
            reply_markup=main_kb())
    except:
        pass
    
    bot.send_message(msg.chat.id, f"❌ Выплата для {target_uid} отклонена")
