/**
 * Notyf notification configuration and behavior.
 *
 * Key behavior:
 * - Single source of truth for toast types/icons.
 * - Manual lifecycle timer per toast so hover pause/reset is real (not only visual).
 * - Progress bar and dismiss timing always stay in sync.
 */

(() => {
    'use strict';

    const DEFAULT_DURATION = 4000;

    const ALERT_TYPES = {
        info: {
            type: 'info',
            className: 'notyf__toast--info',
            icon: `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#6366f1" aria-hidden="true" focusable="false">
                    <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2a10 10 0 100 20 10 10 0 000-20zm0 6a1 1 0 110 2 1 1 0 010-2zm-1 4a1 1 0 000 2h1v4a1 1 0 102 0v-5a1 1 0 00-1-1h-2z"/>
                </svg>
            `.trim()
        },
        warning: {
            type: 'warning',
            className: 'notyf__toast--warning',
            icon: `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" aria-hidden="true" focusable="false">
                    <path fill="#eab308" d="M12 2L1.608 20h20.784L12 2zm-1 7h2v4h-2V9zm0 6h2v2h-2v-2z"/>
                </svg>
            `.trim()
        },
        error: {
            type: 'error',
            className: 'notyf__toast--error',
            icon: `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#ef4444" aria-hidden="true" focusable="false">
                    <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm4.707 13.293a1 1 0 01-1.414 1.414L12 13.414l-3.293 3.293a1 1 0 01-1.414-1.414L10.586 12 7.293 8.707a1 1 0 011.414-1.414L12 10.586l3.293-3.293a1 1 0 011.414 1.414L13.414 12l3.293 3.293z"/>
                </svg>
            `.trim()
        },
        success: {
            type: 'success',
            className: 'notyf__toast--success',
            icon: `
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="#22c55e" aria-hidden="true" focusable="false">
                    <path fill-rule="evenodd" clip-rule="evenodd" d="M12 2C6.477 2 2 6.477 2 12s4.477 10 10 10 10-4.477 10-10S17.523 2 12 2zm-1 13.293-3.707-3.707a1 1 0 111.414-1.414L11 12.172l4.293-4.293a1 1 0 111.414 1.414l-5 5a1 1 0 01-1.414 0z"/>
                </svg>
            `.trim()
        }
    };

    const notyf = new Notyf({
        duration: 0,
        position: { x: 'right', y: 'top' },
        dismissible: true,
        ripple: true,
        types: Object.values(ALERT_TYPES).map((toastType) => ({
            type: toastType.type,
            className: toastType.className,
            background: 'transparent',
            icon: toastType.icon
        }))
    });

    function escapeHtml(value) {
        const div = document.createElement('div');
        div.textContent = value == null ? '' : String(value);
        return div.innerHTML;
    }

    function resolveToastElement(notification) {
        const rendered = notyf.view.notifications.find((item) => item.notification === notification);
        return rendered ? rendered.node : null;
    }

    function createProgressBar() {
        const progressBar = document.createElement('div');
        progressBar.className = 'notyf__progress-bar';
        return progressBar;
    }

    function attachLifecycle(notification, toastElement, duration) {
        const progressBar = createProgressBar();
        toastElement.appendChild(progressBar);

        let isHovered = false;
        let frameId = null;
        let startedAt = performance.now();

        const setProgress = (fraction) => {
            const clamped = Math.max(0, Math.min(1, fraction));
            progressBar.style.transform = `scaleX(${clamped})`;
        };

        const cleanup = () => {
            if (frameId !== null) {
                cancelAnimationFrame(frameId);
                frameId = null;
            }
            toastElement.removeEventListener('mouseenter', handleMouseEnter);
            toastElement.removeEventListener('mouseleave', handleMouseLeave);
        };

        const dismiss = () => {
            cleanup();
            notyf.dismiss(notification);
        };

        const tick = (now) => {
            if (isHovered) {
                frameId = requestAnimationFrame(tick);
                return;
            }

            const elapsed = now - startedAt;
            const remainingFraction = 1 - (elapsed / duration);
            setProgress(remainingFraction);

            if (elapsed >= duration) {
                dismiss();
                return;
            }

            frameId = requestAnimationFrame(tick);
        };

        const handleMouseEnter = () => {
            isHovered = true;
            startedAt = performance.now();
            setProgress(1);
        };

        const handleMouseLeave = () => {
            isHovered = false;
            startedAt = performance.now();
            setProgress(1);
        };

        toastElement.addEventListener('mouseenter', handleMouseEnter);
        toastElement.addEventListener('mouseleave', handleMouseLeave);

        setProgress(1);
        frameId = requestAnimationFrame(tick);

        notification.on('dismiss', cleanup);
    }

    class EnhancedNotyf {
        constructor(notyfInstance) {
            this.notyf = notyfInstance;
        }

        success(message, options = {}) {
            return this.open({ ...options, type: 'success', message });
        }

        error(message, options = {}) {
            return this.open({ ...options, type: 'error', message });
        }

        open(options) {
            const type = options.type || 'info';
            const duration = Number(options.duration) > 0 ? Number(options.duration) : DEFAULT_DURATION;

            const notification = this.notyf.open({
                ...options,
                type,
                duration: 0,
                message: escapeHtml(options.message)
            });

            const toastElement = resolveToastElement(notification);
            if (toastElement) {
                attachLifecycle(notification, toastElement, duration);
            }

            return notification;
        }

        dismiss(notification) {
            this.notyf.dismiss(notification);
        }

        dismissAll() {
            this.notyf.dismissAll();
        }
    }

    const enhancedNotyf = new EnhancedNotyf(notyf);

    function mapCategoryToType(category) {
        switch (category) {
            case 'success':
                return 'success';
            case 'error':
            case 'danger':
                return 'error';
            case 'warning':
                return 'warning';
            case 'info':
            default:
                return 'info';
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        if (!window.FLASH_MESSAGES) return;

        window.FLASH_MESSAGES.forEach(([category, message]) => {
            const notificationType = mapCategoryToType(category);
            enhancedNotyf.open({ type: notificationType, message });
        });
    });

    window.notyf = enhancedNotyf;
    window.notyfReady = true;
})();
