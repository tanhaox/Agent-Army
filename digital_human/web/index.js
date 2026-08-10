    // ── Step Navigation ──
    function scrollToStep(n) {
      const el = document.getElementById(`step-${n}-card`);
      if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function updateStepIndicator(step) {
      document.querySelectorAll('.step-dot').forEach((dot, i) => {
        dot.classList.remove('active', 'done');
        if (i + 1 < step) dot.classList.add('done');
        else if (i + 1 === step) dot.classList.add('active');
      });
      document.querySelectorAll('.step-line').forEach((line, i) => {
        line.classList.toggle('done', i + 1 < step);
      });
    }

    // ── Toast ──
    function toast(msg, type = 'info') {
      const el = document.getElementById('toast');
      el.textContent = msg;
      el.className = `toast ${type} show`;
      setTimeout(() => el.classList.remove('show'), 4000);
    }

    // ── Patch setStatus to also use toast ──
    const _origSetStatus = setStatus;
    setStatus = function(id, text, isError = false, isSuccess = false) {
      _origSetStatus(id, text, isError, isSuccess);
      if (text) toast(text, isError ? 'error' : (isSuccess ? 'success' : 'info'));
    };

    // ── Patch createArticle to advance step ──
    const _origCreateArticle = createArticle;
    createArticle = async function() {
      await _origCreateArticle();
      if (currentArticle) {
        updateStepIndicator(2);
        scrollToStep(2);
      }
    };

    // ── Patch fetchScript to advance step ──
    const _origFetchScript = fetchScript;
    fetchScript = async function(scriptId) {
      await _origFetchScript(scriptId);
      updateStepIndicator(3);
      scrollToStep(3);
    };

    // ── Intersection Observer for step highlighting ──
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const id = entry.target.id;
          const match = id.match(/step-(\d)-card/);
          if (match) updateStepIndicator(parseInt(match[1]));
        }
      });
    }, { threshold: 0.3 });

    document.querySelectorAll('[id^="step-"][id$="-card"]').forEach(el => observer.observe(el));

    // ── Init: load prompt templates, hosts & voices ──
    loadPromptTemplates();
    loadHosts();
    loadVoices();
