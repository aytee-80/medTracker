from flask import Flask
from flask_mail import Mail
import config
import email_config
import os
from run.db.setup import create_tables
from run.services.scheduler import start_scheduler

mail = Mail()

def create_app():
    # Get the absolute path to the project root (medication_app/)
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    
    app = Flask(
        __name__,
        template_folder=os.path.join(basedir, 'templates'),
        static_folder=os.path.join(basedir, 'static')
    )
    
    app.config['SECRET_KEY'] = config.SECRET_KEY

    # Mail Config
    app.config.update(
        MAIL_SERVER=email_config.EMAIL_HOST,
        MAIL_PORT=email_config.EMAIL_PORT,
        MAIL_USE_TLS=email_config.EMAIL_USE_TLS,
        MAIL_USERNAME=email_config.EMAIL_HOST_USER,
        MAIL_PASSWORD=email_config.EMAIL_HOST_PASSWORD
    )

    # Initialize mail extension
    mail.init_app(app)

    # Register blueprints (no url_prefix to keep original route paths)
    from run.routes import auth, main, meds, stats, misc , ai_assistant
    app.register_blueprint(auth.auth)
    app.register_blueprint(main.main)
    app.register_blueprint(meds.meds)
    app.register_blueprint(stats.stats)
    app.register_blueprint(misc.misc)
    app.register_blueprint(ai_assistant.ai_assistant)

    # Add format_time filter to Jinja2
    from run.utils.helpers import format_time
    app.jinja_env.filters['format_time'] = format_time

    # Create database tables
    create_tables(app)

    # Start background scheduler
    start_scheduler(app, mail)

    return app