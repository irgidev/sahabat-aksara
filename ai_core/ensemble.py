"""
Ensemble Scorer V7 — Clean Slate
=================================
Philosophy:
- Skeleton = 55% (KING of shape discrimination)
- Structural = 25% (GUARDIAN: must have right features)
- HOG + SSIM + Distance + Completeness + StrokeCount = 20% total (supporting only)
- Boost curve: max +8 points (let natural scores speak)
- Skeleton gate: wrong shape gets multiplier penalty
"""

import json
import os

from .scorers import SCORER_REGISTRY


class EnsembleScorer:
    def __init__(self, config_path=None):
        if config_path is None:
            config_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                'ensemble_config.json'
            )
        self.config_path = config_path
        self.config = self._load_config()
        self.scorers = {}
        self._init_scorers()



    def _load_config(self):
        default = {
            'global_weights': {
                'skeleton':       0.55,
                'structural':      0.25,
                'hog':             0.06,
                'ssim':            0.06,
                'distance':        0.03,
                'completeness':    0.03,
                'stroke_count':    0.02,
            },
            'character_overrides': {},
            'scorer_config': {
                'skeleton': {'tolerance_px': 5},
            },
            'boost_enabled': True,
        }
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            default.update(cfg)
            return default
        except Exception:
            return default



    def _init_scorers(self):
        for name, cls in SCORER_REGISTRY.items():
            self.scorers[name] = cls(self.config)



    def evaluate(self, user_img, template_img, char_target='A', **kwargs):
        scores = {}


        for name, scorer in self.scorers.items():
            try:
                score_val, detail = scorer.score(
                    user_img, template_img,
                    char_target=char_target, **kwargs
                )
                scores[name] = (score_val, detail)
            except Exception as e:
                scores[name] = (0.0, {'error': str(e)[:80]})


        final_score = self.combine(scores, char_target)


        skel = scores.get('skeleton', (0, {}))[0]
        confidence = 'high' if skel > 65 else ('medium' if skel > 40 else 'low')


        tip = self._generate_tip(final_score, char_target)

        return final_score, confidence, tip, scores



    def combine(self, scores, char_target='A'):
        weights = dict(self.config['global_weights'])


        overrides = self.config.get('character_overrides', {}).get(char_target.upper(), {})
        weights.update(overrides)

        raw_final = 0.0
        total_weight = 0.0

        print(f'[v7 Eval] char={char_target}')
        for name, (score_val, detail) in sorted(scores.items()):
            w = weights.get(name, 0)
            contribution = score_val * w
            raw_final += contribution
            total_weight += w
            print(f'        {name:>12} = {score_val:>6.1f}% (w={w:.2f}) -> {contribution:>5.1f}pts')

        if total_weight > 0:
            raw_final /= total_weight


        if self.config.get('boost_enabled', True):
            final_score = self._minimal_boost(raw_final)
        else:
            final_score = raw_final


        skel_score = scores.get('skeleton', (0, {}))[0]
        struct_score = scores.get('structural', (0, {}))[0]
        


        shape_agrees = (skel_score >= 55 and struct_score >= 50)
        
        if skel_score < 28:

            final_score *= 0.20
        elif not shape_agrees:

            final_score *= 0.42
        elif skel_score < 52:

            final_score *= 0.62

        final_score = max(0, min(100, round(final_score, 1)))

        print(f'  >>> FINAL = {final_score} (confidence based on skeleton={skel_score:.1f}%)')
        print(f'  >>> TIP: {self._generate_tip(final_score, char_target)}')

        return final_score



    def _minimal_boost(self, raw_score):
        """
        V7: Very gentle boost. Max +8 points.
        Don't inflate bad scores into good ones.
        """
        raw_score = max(0, min(100, raw_score))

        if raw_score >= 75:

            return min(100, raw_score + 4)
        elif raw_score >= 55:

            return raw_score + 3
        elif raw_score >= 35:

            return raw_score + 2
        else:

            return max(raw_score * 1.1, 3)



    TIPS = {
        (80, 101): "Luar biasa! Kamu hebat sekali!",
        (65, 80):  "Bagus sekolah! Huruf {char} sudah mirip lho. Terus ya!",
        (45, 65):  "Lumayan! Ayo coba lagi tulis huruf {char}, pasti bisa lebih baik!",
        (25, 45):  "Tidak apa-apa! Setiap anak pintar itu berlatih. Huruf {char} butuh latihan lagi!",
        (10, 25):  "Jangan menyerah! Coba perhatikan contoh huruf {char}, lalu tulis pelan-pelan!",
        (0, 10):   "Yuk kita coba lagi dari awal! Pasti bisa!",
    }

    def _generate_tip(self, score, char_target):
        for (lo, hi), tip in self.TIPS.items():
            if lo <= score < hi:
                return tip.format(char=char_target)
        return "Terus berlatih ya!"
